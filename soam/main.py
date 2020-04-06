
from helpers import AttributeHelperMixin
from series import SeriesManager

EXTRACT_SQL_TPL = '''
SELECT
    attrs['provider'] as ad_network,
    attrs['provider_placement'] as placement_id,
    from_unixtime(client_time, 'yyyy-MM-dd') as ds,
    sum(if(event_name = 'ads:cache-request', 1, 0)) as cache_requests,
    sum(if(event_name = 'ads:view-request', 1, 0)) as view_requests,
    sum(if(event_name = 'ads:view-start', 1, 0)) as view_starts,
    sum(if(event_name = 'ads:cache-success', 1, 0)) as cache_successes
FROM {table}
WHERE
  (
      year >= '{start_date_year}' AND
      month >= '{start_date_month}' AND
      day >= '{start_date_day}'
  ) AND
  (
      year <= '{end_date_year}' AND
      month <= '{end_date_month}' AND
      day <= '{end_date_day}'
  ) AND
  AND game = '{game}'
  AND concat(year, '-', month, '-', day) = from_unixtime(client_time, 'yyyy-MM-dd')
group by 1,2,3
order by 2 asc, 3 asc
'''

class Extractor(AttributeHelperMixin):
    # def __init__(self, game, dimensions_l, factor_mgr):
        # self.dimensions_l = dimensions_l
    def __init__(self, game, factor_mgr):
        self.game = game
        self.factor_mgr = factor_mgr

    def extract(self, time_range_conf):        
        start_date_year = time_range_conf.start_date.strftime('%Y')
        start_date_month = time_range_conf.start_date.strftime('%m')
        start_date_day = time_range_conf.start_date.strftime('%d')
        end_date_year = time_range_conf.end_date.strftime('%Y')
        end_date_month = time_range_conf.end_date.strftime('%m')
        end_date_day = time_range_conf.end_date.strftime('%d')
        sql = EXTRACT_SQL_TPL.format(
            start_date_year=start_date_year,
            start_date_month=start_date_month,
            start_date_day=start_date_day,
            end_date_year=end_date_year,
            end_date_month=end_date_month,
            end_date_day=end_date_day,
            game=self.game,
        )
        raw_data = spark.sql(sql).toPandas()
        series_mgr = SeriesManager(raw_data)
        return series_mgr

from series import SeriesManager

def run_series_pipeline(kpi, time_range_conf, extractor, factor_mgr):
    """Extract and transform a given series."""
    series_dict = extractor.extract(time_range_conf)
    # series_dict = KPISeriesPreprocBase.build_from_kpi(kpi).preproc(series_dict)
    series_mgr = SeriesManager(series_dict)
    # series_mgr.transform(kpi, time_range_conf.time_granularity, factor_mgr)
    # series_mgr.build_regressors()
    factor_mgr.process(kpi.target_series, series_mgr)
    return series_mgr, factor_mgr

from datetime import datetime
from soam.helpers import TimeRangeConfiguration

from constants import DAILY_TIME_GRANULARITY

class KPI:
    def __init__(self, target_series, target_col, name, anomaly_plot_ylabel, mail_kpi, name_spanish):
        self.target_series = target_series 
        self.target_col = target_col
        self.name = name
        self.anomaly_plot_ylabel = anomaly_plot_ylabel
        self.mail_kpi = mail_kpi
        self.name_spanish = name_spanish

kpi = KPI(
        target_series = "cache_successes",
        target_col = "cache_successes",
        name = "cache_successes",
        anomaly_plot_ylabel = "cache_successes",
        mail_kpi = "cache_successes",
        name_spanish = "cache_successes",
)

# Create tables


def main():
    FORECASTER_FUTURE_WINDOW = 15
    FORECASTER_FUTURE_WINDOW_CUMSUM_KPI = 30
    FORECASTER_TRAIN_WINDOW = 90
    ANOMALY_WINDOW = 7
    CLF_TRAIN_WINDOW = 7
    SAMPLE_SIZE = 2
    TOP_K_INFLUENCERS = 12

    execution_date = datetime.strptime('2020-04-01', '%Y-%m-%d')
    time_range_conf = TimeRangeConfiguration(
        end_date=execution_date,
        forecast_train_window=30,
        forecast_future_window=FORECASTER_FUTURE_WINDOW,
        time_granularity=DAILY_TIME_GRANULARITY,
        anomaly_window=ANOMALY_WINDOW,
        end_hour=0,
    )




if __name__ == "__main__":
    main()

