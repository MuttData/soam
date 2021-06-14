"""
Module to extract and aggregate time series.

# General TODOs:
- Make quantiles great again:
  https://gitlab.com/mutt_data/tfg-adsplash/-/blob/master/adsplash/store/dataset.py
  They are a nice feature but couldn't get them to work yet.

Notes:
- Dimensional hierarchy can be implemented via snowflake schema [1].
    We could implement this idea via "virtual dimensions" that are really the values we get from
    joining higher in the hierarchy.
- It would be interesting to implement unique counts.

[1] Ralph Kimball, Margy Ross - The Data Warehouse Toolkit (2013).
"""
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from jinja2 import Template
import pandas as pd

from soam.constants import (
    DONT_AGGREGATE_SYMBOL,
    NEGATE_SYMBOL,
    TIMESTAMP_COL,
    regex_prefix_symbols,
)
from soam.core import Step

if TYPE_CHECKING:
    import datetime as dt

    import muttlib

# Simple column selection templates.
BASE_TEMPLATE = """
    {{ column }} AS {{ alias }}
"""

COMPUTE_SHARE_COLUMN_TEMPLATE = """
    COALESCE(
        {{ constant if constant else 1.0 }} * {{denominator}}::float8 / NULLIF({{numerator}}, 0), 0
    ) AS {{ alias }}
"""

MAX_TEMPLATE = """
    MAX({{ column }})::float8 AS {{ alias }}
"""
SUM_TEMPLATE = """
    SUM({{ column }})::float8 AS {{ alias }}
"""

JOIN_TEMPLATE = """
    JOIN {{table}} ON {{condition}}
"""


class TimeSeriesExtractor(Step):
    db: "muttlib.dbconn.BaseClient"
    table_name: str
    build_query_kwargs: Dict[str, Any]

    def __init__(
        self,
        db: "muttlib.dbconn.BaseClient",
        table_name: str,
        **kwargs: Dict[str, Any],
    ):
        """
        Class to handle the dataset retrieval from the PostgreSql database.

        Parameters
        ----------
        db: muttlib.dbconn.BaseClient
            The database connection to use.
        table_name: str
            The table's name.
        """
        super().__init__(**kwargs)
        self.db = db
        self.table_name = table_name
        self.build_query_kwargs = {}  # this needs to be passed as a param

    def get_params(self, deep=True):
        d = super().get_params(deep)
        d["db_conn_str"] = self.db.conn_str
        del d["db"]
        d["build_query_kwargs"] = self.build_query_kwargs
        return d

    def extract(self, build_query_kwargs: Dict[str, Any],) -> pd.DataFrame:
        """
        Extracts aggregated data and return it as a pandas DataFrame.

        Parameters
        ----------
        build_query_kwargs: dict of {str: obj}
            Configuration of the extraction query to be used for the extraction.

        Returns
        -------
        pd.DataFrame
            Extracted data.
        """
        query, kwargs = self.build_query(**build_query_kwargs)
        conn = self.db._connect()  # pylint: disable=protected-access
        df = self.db.to_frame(query, connection=conn, **kwargs)
        if df.empty:
            df = pd.DataFrame(columns=build_query_kwargs["columns"])
        conn.close()
        return df

    # maybe define class type all this arguments?
    def build_query(
        self,
        table_mapping: str = None,
        columns=None,
        prequery: str = "",
        dimensions: List[str] = None,
        dimensions_values: List[str] = None,
        timestamp_col: str = TIMESTAMP_COL,
        start_date: Union["dt.datetime", str] = None,
        end_date: Union["dt.datetime", str] = None,
        order_by: List[str] = None,
        extra_where_conditions: List[str] = None,
        extra_having_conditions: List[str] = None,
        column_mappings: Dict = None,
        aggregated_column_mappings: Dict = None,
        inner_join: Optional[List[Tuple[str, str, str]]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Build the query to extract and aggregated dataset.

        Parameters
        ----------
        table_mapping: str
            The alias of the table.
        columns: list of str
            The columns to retrieve.
        prequery: str
            Query to prepend to the output.
        dimensions: list of str
            The dimensions by which data will be partitioned / aggregated.
            E.g.: ['year', 'month', 'day', 'game', 'type'].
            If a dimension is prefixed with a "!", the dimensions values will
            be negated and the complement rows will be returned.
            E.g.: ['!country'] with ['US'] would return the rows of every
            country except the US.
            If a dimensions is prefixes with a "#", the dimensions values won't
            be used as a group by but as a filter.`
        dimensions_values: str or list of str
            Values to filter the dataset with the indexes matching the
            dimensions indexes.
            If a list is provided for a dimension, all values will be
            considered valid with an OR operator.
            "*" and None won't filter the results.
            However "*" will be recorded as an estimator's / optimizer's
            dimension in the database for record, None won't.
            E.g. for the example dimensions above:
            [2019, 9, None, 'android_flightpilot', 'interstitial']
            would only return september 2019 instertitials data for flight
            pilot android.
            E.g.: doing ['country'], [['BR', 'US']] would return every row
            that is from either BR or US.
        timestamp_col: str
            Name of the column what will hold the timestamp of the fact.
        start_date: datetime
            A start date to filter the rows.
        end_date: datetime
            An inclusive end date to filter the rows.
        order_by:  list of str
            A list of column names to order by.
        extra_where_conditions: list of str
            A list of conditions to be added to the "where" clause.
        extra_having_conditions:  list of str or None
            A list of conditions to be added to the "having" clause.
        column_mappings: dict
            A dict with 'column names' as keys and 'column as column alias' as values.
            E.g.: A dict like {'date':'date as fecha'} would result in
            a SQL statement 'SELECT date as fecha'.
        aggregated_column_mappings: dict
            Contains the aggregation functions and aliases to replace the column
            values.
        inner_join: list of tuple of int
            A list of tables to join on, every tuple is expected to contain:
            (table_name, table_alias, complete_condition).
            The table_alias is optional.
            For example:
            [('table_a', 'at', 'initial_table_model.attr_1 = at.attr_1'),
            ('table_b', 'BBB', 'initial_table_model.attr_2 = BBB.222'),
            ('table_c', None, 'initial_table_model.attr_3 = table_c.attr_3')]

        Returns
        -------
        tuple of (str, dict of {str: obj})
            Renderd SQL query to extract data.
        """

        args_maybe_dt = [start_date, end_date]

        for arg in args_maybe_dt:
            arg = pd.to_datetime(arg)

        # Template
        query = """
          {{ prequery }}
          SELECT {{ columns | join(", ") }}
          FROM {{ table_name }}
          {% if table_mapping %}
          AS {{ table_mapping }}
          {% endif %}
          {% if join_tables %}
          {% for j_table in join_tables %}
          INNER JOIN {{ j_table.0 }}
          {% if j_table.1 %}
          AS  {{ j_table.1 }}
          {% endif %}
          ON  {{ j_table.2 }}
          {% endfor %}
          {% endif %}
          {% if where %}
          WHERE {{ where | join(" AND ") }}
          {% endif %}
          {% if group_by %}
          GROUP BY {{ group_by | join(", ") }}
          {% endif %}
          {% if having %}
          HAVING {{ having | join(" AND ") }}
          {% endif %}
          {% if order_by %}
          ORDER BY {{ order_by | join(", ") }}
          {% endif %}
        """
        kwargs: Dict[str, Union[int, float, str]] = {}

        if column_mappings is None:
            column_mappings = {}
        if aggregated_column_mappings is None:
            aggregated_column_mappings = {}

        placeholders = {
            "prequery": prequery,
            "columns": "*",
            "table_name": self.table_name,
            "table_mapping": table_mapping,
            "join_tables": inner_join,
            "where": "",
            "group_by": "",
            "having": "",
            "order_by": "",
        }

        # Dimensions negation and check if disable dimension aggregation
        ((dimensions, negate_dimensions_values), (_, dont_aggregate_dimensions)) = (
            self._negate_dimensions(dimensions),
            self._dont_aggregate_dimensions(dimensions),
        )

        # Columns
        col_map = aggregated_column_mappings
        if dimensions is None or all(dont_aggregate_dimensions):
            col_map = column_mappings

        columns = [col_map.get(col, col) for col in columns]

        placeholders["columns"] = columns

        # Where
        where_conds: List[str] = []
        values_conds, values_kwargs = self._filter_dimensions_values(
            dimensions, dimensions_values, negate_dimensions_values,
        )
        kwargs.update(values_kwargs)
        where_conds.extend(values_conds)
        date_conds, date_kwargs = self._filter_date_range(
            start_date, end_date, timestamp_col=timestamp_col
        )
        kwargs.update(date_kwargs)
        where_conds.extend(date_conds)
        if extra_where_conditions:
            extra_where_conditions = [
                cond.replace("%", "%%")
                for cond in extra_where_conditions
                if "%" in cond
            ]
            where_conds.extend(extra_where_conditions)
        if where_conds:
            placeholders["where"] = where_conds  # type: ignore

        # Having
        having_conds = []
        if extra_having_conditions:
            having_conds.extend(extra_having_conditions)
        if having_conds:
            placeholders["having"] = having_conds  # type: ignore

        # Group by
        if dimensions is not None:
            placeholders["group_by"] = [
                dim  # type: ignore
                for dim, dont in zip(dimensions, dont_aggregate_dimensions)
                if not dont
            ]
        # Order by
        if order_by is not None:
            placeholders["order_by"] = order_by  # type: ignore

        # Render
        sql = Template(query).render(**placeholders)
        kwargs = {
            k: v if not isinstance(v, str) else f"'{v}'" for k, v in kwargs.items()
        }
        # FIXME: Formatting SQL like this is unsafe. We should pass the params to the
        # engine along the query.
        sql = sql % kwargs
        kwargs = {}
        return sql, kwargs

    def dimensions_values(
        self,
        dimensions,
        dimensions_values=None,
        start_date=None,
        end_date=None,
        order_by=None,
    ):
        """
        Returns the values for the dimensions provided in the dataset.

        Parameters
        ----------
        dimensions:  list of str
            The column names which dimensions values wants to be retrieved.
            E.g.: ['game', 'type'].
        dimensions_values:  str or list of str or None or "*"
            Values to filter the dataset with the indexes matching the
            dimensions indexes.
            If a list is provided for a dimension, all values will be
            considered valid with an OR operator.
            E.g.:
            dimensions=['country', 'ad_network']
            dimensions_values=['us', None]
            Would return all the ('us', ad_network) pairs.
            Or [['br', 'us'], None] would return all pairs of
            (country, ad_network) with the country being one of br or us.
        start_date: datetime
            A start date to filter the rows.
        end_date: datetime
            An inclusive end date to filter the rows.
        order_by:  list of str
            A list of column names to order by.

        Returns
        -------
        list of [tuple of str]
            A list of tuples with the requested columns.
            E.g.: [('android_flightpilot', 'instertitial',
                   ('android_flightpilot', 'rewardedVideo')]
        """
        # Template
        kwargs = {}
        query = """
          SELECT DISTINCT {{ columns | join(", ") }}
          FROM {{ table_name }}
          {% if where %}
          WHERE {{ where | join(" AND ") }}
          {% endif %}
          {% if order_by %}
          ORDER BY {{ order_by | join(", ") }}
          {% endif %}
        """
        placeholders = {
            "columns": dimensions,
            "table_name": self.table_name,
            "where": "",
            "group_by": dimensions,
            "order_by": "",
        }
        # Dimensions negation
        dimensions, negate_dimensions_values = self._negate_dimensions(dimensions)

        # Where
        where_conds, kwargs = self._filter_date_range(start_date, end_date)
        values_conds, values_kwargs = self._filter_dimensions_values(
            dimensions, dimensions_values, negate_dimensions_values,
        )
        kwargs.update(values_kwargs)
        where_conds.extend(values_conds)
        placeholders["where"] = where_conds

        # Order by
        placeholders["order_by"] = order_by

        # Render
        sql = Template(query).render(**placeholders)
        for k, v in kwargs.items():
            if isinstance(v, str):
                kwargs[k] = f"'{v}'"
            elif isinstance(v, tuple):
                if isinstance(v[0], str):
                    v = (f"'{v_i}'" for v_i in v)
                v = ", ".join(v)
                kwargs[k] = f"({v})"

        sql = sql % kwargs
        ret = [list(row) for row in self.db.execute(sql, params=kwargs)]
        return ret

    def _filter_date_range(
        self, start_date=None, end_date=None, timestamp_col=TIMESTAMP_COL,
    ):
        """
        Returns a list of conditions for a where clause and a dictionary
        with keyword arguments to fill the conditions parameters.

        Parameters
        ----------
        start_date: datetime
            A start date to filter the rows.
        end_date: datetime
            An inclusive end date to filter the rows.

        Returns
        -------
        tuple of (list of str, dict())
             list of str: list of sql conditions for filtering.
            dict: dictionary holding the values of the placeholders in the
                  conditions.
        """
        conds = []
        kwargs = {}
        if start_date is not None:
            conds.append(f"{timestamp_col} >= %(start_date)s")
            kwargs["start_date"] = start_date
            if not isinstance(start_date, str):
                kwargs["start_date"] = start_date.strftime("%Y-%m-%d")
        if end_date is not None:
            conds.append(f"{timestamp_col} <= %(end_date)s")
            kwargs["end_date"] = end_date
            if not isinstance(end_date, str):
                kwargs["end_date"] = end_date.strftime("%Y-%m-%d")
        return conds, kwargs

    def _negate_dimensions(self, dimensions):
        """
        Returns dimensions without the prefix symbols and a boolean list
        indication if they have to be negated.

        Parameters
        ----------
        dimensions:  list of str or None
            A list of dimension names

        Returns
        -------
        tuple of (list of str, list of bool)
            * List of dimension names with the negatino prefixes "!" removed.
            * List of boolean values indicating if the dimension has to be
              negated or not
        """
        return self._detect_dimensions_prefix_symbol(dimensions, NEGATE_SYMBOL)

    def _dont_aggregate_dimensions(self, dimensions):
        """
        Returns dimensions without the prefix symbols and a boolean list
        indication if they don't have to be aggregated.

        Parameters
        ----------
        dimensions:  list of str or None
            A list of dimension names

        Returns
        -------
        tuple of (list of str, list of bool)
            * List of dimension names with the negatino prefixes "#" removed.
            * List of boolean values indicating if the dimension should not be
              aggregated.
        """
        return self._detect_dimensions_prefix_symbol(dimensions, DONT_AGGREGATE_SYMBOL)

    def _detect_dimensions_prefix_symbol(
        self, dimensions, prefix_symbol,
    ):
        """
        Returns dimensions with the prefix symbols removed and a boolean
        list indication if they are prefixed with it.

        Parameters
        ----------
        dimensions:  list of str or None
            A list of dimension names
        prefix_symbol: str
            The prefix symbol (a character) that we want to check if it
            prefixes the dimension name.

        Returns
        -------
        tuple of (list of str, list of bool)
            * List of dimension names with the prefix symbol removed.
            * List of boolean values indicating if the dimension was prefixed
              with the symbol.
        """
        if dimensions:
            has_symbol = []
            # Find symbol
            for dimension in dimensions:
                if dimension:
                    match = regex_prefix_symbols.match(dimension)
                    has_symbol.append(match and prefix_symbol in match[0])
            # Remove prefixes from dimensinos
            dimensions = [
                regex_prefix_symbols.sub("", dimension) for dimension in dimensions
            ]
            return dimensions, has_symbol
        return dimensions, None

    def _filter_dimensions_values(
        self, dimensions, dimensions_values, negate_dimensions_values,
    ):
        """
        Returns a list of conditions for a where clause and a dictionary
        with keyword arguments to fill the conditions parameters.

        Parameters
        ----------
        dimensions:  list of str or None
            A list of dimension names
        dimensions_values: obj or list of obj or None
            A list with the wanted values for the dimensions.
        negate_dimensions_values: list of bool
            List of boolean values indicating if the dimension has to be
            negated or not

        Returns
        -------
        tuple of (list of str, dict of {str : obj})
             list of str: list of sql conditions for filtering.
            dict: dictionary holding the values of the placeholders in the
                  conditions.
        """
        conds = []
        kwargs = {}
        if dimensions is not None and dimensions_values is not None:
            for name, value, negate in zip(
                dimensions, dimensions_values, negate_dimensions_values
            ):
                # Can we use a standard parsable language instead of this? pyparsing?
                # https://github.com/pyparsing/pyparsing/blob/master/examples/simpleBool.py
                if value is not None and value != "*":
                    operators = ("!=", "NOT IN") if negate else ("=", "IN")
                    if isinstance(value, (list, tuple)):
                        conds.append("%s %s %%(%s)s" % (name, operators[1], name))
                        kwargs[name] = tuple(value)
                    else:
                        conds.append("%s %s %%(%s)s" % (name, operators[0], name))
                        kwargs[name] = value
        return conds, kwargs

    def run(self, build_query_kwargs: Dict[str, Any]) -> pd.DataFrame:  # type: ignore
        """
        Returns aggregated data from a query into a pandas DataFrame.

        Parameters
        ----------
        build_query_kwargs: dict

        Returns
        -------
        pd.DataFrame
            Agregated data from the time series extractor object.
        """
        return self.extract(build_query_kwargs)
