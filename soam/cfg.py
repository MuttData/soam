
# cfg.py
from pathlib import Path
from soam.utils import template, make_dirs

KPI_TABLE_BASENAME = "kpis"
DELVER_RUN_TABLE_BASENAME = "delver_runs"
DELVER_RUN_FACTOR_CONF_TABLE_BASENAME = "delver_run_factor_conf"
FORECASTER_RUNS_TABLE_BASENAME = "forecaster_runs"
FORECASTER_VALUES_TABLE_BASENAME = "forecaster_values"
INFLUENCER_RUNS_TABLE_BASENAME = "influencer_runs"
INFLUENCER_VALUES_TABLE_BASENAME = "influencer_values"
DRILL_DOWN_RUNS_TABLE_BASENAME = "drill_down_runs"
DRILL_DOWN_VALUES_TABLE_BASENAME = "drill_down_values"
COSERIES_RUNS_TABLE_BASENAME = "coseries_runs"
COSERIES_DIMENSIONS_TABLE_BASENAME = "coseries_dimensions"
COSERIES_VALUES_TABLE_BASENAME = "coseries_values"
COSERIES_SCORES_TABLE_BASENAME = "coseries_scores"
TIMELINE_TABLE_BASENAME = "timeline"

# Setup paths
# _p = Path(__file__).resolve().parent
_p = Path("/tmp/anomalies/")
SQL_DIR = make_dirs(Path(_p, "resources"))
LOG_DIR = make_dirs(Path(_p, "tmp", "logs"))
DATA_DIR = make_dirs(Path(_p, "tmp", "data"))
DATA_DIR_TABULAR = make_dirs(Path(_p, "tmp", "data", "tabular"))
FIG_DIR = make_dirs(Path(_p, "tmp", "figures"))
RES_DIR = make_dirs(Path(_p, "tmp", "results"))

#SQL_TEMPLATE = utils.template(
#    str((_p / "resources" / "templates.sql").resolve())
#).module

# Table name setup
table_name_preffix = ""

# if ENV is not None:
#     table_name_preffix = f"{ENV}_"
table_name_preffix = ""

KPI_TABLE = f"{table_name_preffix}{KPI_TABLE_BASENAME}"
DELVER_RUN_TABLE = f"{table_name_preffix}{DELVER_RUN_TABLE_BASENAME}"
DELVER_RUN_FACTOR_CONF_TABLE = (
    f"{table_name_preffix}{DELVER_RUN_FACTOR_CONF_TABLE_BASENAME}"
)
FORECASTER_RUNS_TABLE = f"{table_name_preffix}{FORECASTER_RUNS_TABLE_BASENAME}"
FORECASTER_VALUES_TABLE = f"{table_name_preffix}{FORECASTER_VALUES_TABLE_BASENAME}"
INFLUENCER_RUNS_TABLE = f"{table_name_preffix}{INFLUENCER_RUNS_TABLE_BASENAME}"
INFLUENCER_VALUES_TABLE = f"{table_name_preffix}{INFLUENCER_VALUES_TABLE_BASENAME}"
DRILL_DOWN_RUNS_TABLE = f"{table_name_preffix}{DRILL_DOWN_RUNS_TABLE_BASENAME}"
DRILL_DOWN_VALUES_TABLE = f"{table_name_preffix}{DRILL_DOWN_VALUES_TABLE_BASENAME}"
COSERIES_RUNS_TABLE = f"{table_name_preffix}{COSERIES_RUNS_TABLE_BASENAME}"
COSERIES_DIMENSIONS_TABLE = f"{table_name_preffix}{COSERIES_DIMENSIONS_TABLE_BASENAME}"
COSERIES_VALUES_TABLE = f"{table_name_preffix}{COSERIES_VALUES_TABLE_BASENAME}"
COSERIES_SCORES_TABLE = f"{table_name_preffix}{COSERIES_SCORES_TABLE_BASENAME}"
TIMELINE_TABLE = f"{table_name_preffix}{TIMELINE_TABLE_BASENAME}"

# Mail report
MAIL_TEMPLATE_BODY = """
{% macro mail_body(kpi, end_date, img_dict={}, anomaly_range_stats={}, anomaly_window=none, granularity=None, time_granularity=None) %}
<!DOCTYPE html>
<head>
  <meta charset='UTF-8'>
  <title>Ads Monetization events performance Anomaly Detection report</title>
  <style type='text/css'>

    .maindiv {
      height: 100%;
      width:100% !important;
      background-color: #f7f7f7;
      margin: 0;
      padding: 0;
      overflow: auto;
    }

    .contentdiv {
      background-size: cover;
      background-color: #ffffff;
      width: 90%;
      margin: 14px auto 0 auto;
      padding: 14px;
    }

    .header {
      font-size: 16px;
      line-height: 22px;
      font-family: 'Open Sans','Helvetica Neue',Helvetica,Arial,sans-serif;
      color: #666;
      background: #fff;
    }

    .underline {
      width: 100px;
      border-bottom: 2px solid #FF9900;
      margin-top: 10px;
    }

    img, a img {
      margin: 0px 0 10px 0;
      border: 0;
      outline: none;
      text-decoration: none;
    }

    p {
      margin: 1em 0;
      padding: 0;
      font-family: 'Open Sans','Helvetica Neue',Helvetica,Arial,sans-serif;
      color: #666;
    }

    .subtitle {
      font-size: 24px;
      text-align: left;
    }

    body, table, td, p, a, li, blockquote {
      -ms-text-size-adjust: 100%;
      -webkit-text-size-adjust: 100%;
    }

    .footer {
      margin-bottom: 15px;
      margin-top: 15px;
      text-align: left;
      font-size: 16px;
      line-height: 22px;
      font-family: 'Open Sans','Helvetica Neue',Helvetica,Arial,sans-serif;
      color: #666;
      background: #fff;
    }

    .footer img,
    .footer span {
      display: inline-block;
      vertical-align: middle;
    }

    table {
      font-family: 'Open Sans','Helvetica Neue',Helvetica,Arial,sans-serif;
      font-size: 16px;
      color: #666;
      border: solid 1px;
      border-collapse: collapse;
      border-spacing: 0;
    }
    table td, table th  {
      padding: 8px;
    }

  </style>
</head>
<body>

  <div class='maindiv'>
  <div class='contentdiv'>
    <div class='header'>
        <span>Hi there,</span>
        <p>Take a look at the anomalies anomalies found for the last {{ anomaly_window }} days of the <b>KPI {{ kpi }}</b>.</p>
    </div>
        

    <p><b>The news for yesterday ({{ end_date }}) are: we detected {{
      anomaly_range_stats.get('nr_anomalies_news')}}
      {% if anomaly_range_stats.get('nr_anomalies_news') > 0 %}
        ({{ anomaly_range_stats.get('pos_anomalies_news') }} positive and
        {{ anomaly_range_stats.get('neg_anomalies_news') }} negative)
      {% endif %}
      anomalies.
    </b></p>
    
    <p>
      Summary for the last {{ anomaly_window }} days (including yesterday):
      <ul>
        <li>{{ anomaly_range_stats.get('nr_anomalies') }} anomalies
        {% if anomaly_range_stats.get('nr_anomalies') > 0 %}:
          {{ anomaly_range_stats.get('pos_anomalies') }} positive and
          {{ anomaly_range_stats.get('neg_anomalies') }} negative
        {% endif %}
        </li>
      {% if anomaly_range_stats.get('nr_anomalies') > 0 %}
        <li>There were {{ anomaly_range_stats.get('anomaly_dates')}} temporal instances
          with anomalies</li>
        <li>The most significant one was on the {{ anomaly_range_stats.get('worst_anomaly') }}</li>
      {% endif %}
      </ul>
    </p>
    
    {% if anomaly_range_stats.get('nr_anomalies') > 0 %}
    <p>
      Details for the days with anomalies:<br />
        <center>
        {{ anomaly_range_stats.get('anomaly_summary') }}
        </center>
        <br />
        {% for granularity_val in img_dict
        ['outliers'] %}
            <span class='subtitle'>Analysis for {{ granularity_val }}</span>
            <div class='underline'></div>
            <div>
                <img src='cid:{{ img_dict['outliers'][granularity_val] }}' />
            </div>
            <div>
                <img src='cid:{{ img_dict['extra'][granularity_val] }}' />
            </div>
        {% endfor %}
    </p>
    {% endif %}

    <div class='footer'>
        <span>Cheers,</span>
        <span>Anomaly Detector</span>
    </div>
</div>
</div>
</body>
</html>
{% endmacro %}
"""
MAIL_TEMPLATE = template(
    MAIL_TEMPLATE_BODY
).module
