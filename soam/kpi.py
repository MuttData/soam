class KPI:
    def __init__(
        self,
        target_series,
        target_col,
        name,
        anomaly_plot_ylabel,
        mail_kpi,
        name_spanish,
    ):
        self.target_series = target_series
        self.target_col = target_col
        self.name = name
        self.anomaly_plot_ylabel = anomaly_plot_ylabel
        self.mail_kpi = mail_kpi
        self.name_spanish = name_spanish
