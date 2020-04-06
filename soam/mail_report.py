"""Mail creator and sender."""
import io
import logging
import smtplib
from datetime import timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd


from forecast_plotter import anomaly_plot
from cfg import MAIL_TEMPLATE
from constants import (
    DAILY_TIME_GRANULARITY,
    DS_COL,
    HOURLY_TIME_GRANULARITY,
    MAIL_WORST_FACTOR_VALS_NR,
    PARENT_LOGGER,
    # PROVINCIAL_GEO_GRANULARITY,
)
from forecaster import OUTLIER_SIGN_COL, OUTLIER_VALUE_COL, forecasts_fig_path
from helpers import AttributeHelperMixin


logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")


def send_mail(smtp_credentials, mail_recipients, subject, mail_body, mime_image_list):
    """Send."""
    user = smtp_credentials.get("user_address")
    password = smtp_credentials.get("password")
    from_address = f"Anomalias <{smtp_credentials['mail_from']}>"
    msg_root = MIMEMultipart("related")
    msg_root["From"] = from_address
    msg_root["Subject"] = subject
    msg_root["To"] = ", ".join(mail_recipients)

    msg_alt = MIMEMultipart("alternative")
    msg_root.attach(msg_alt)

    msg_text = MIMEText(mail_body, "html")
    msg_alt.attach(msg_text)

    for mim_img in mime_image_list:
        msg_root.attach(mim_img)

    user = smtp_credentials.get("user_address")
    password = smtp_credentials.get("password")
    with smtplib.SMTP(smtp_credentials["host"], smtp_credentials["port"]) as server:
        server.ehlo()
        if user is not None and password is not None:
            server.starttls()
            server.ehlo()
            server.login(user, password)
        server.sendmail(from_address, mail_recipients, msg_root.as_string())
    logger.info("Email sent succesfully")


def _build_subject_n_msg_body(
    kpi,
    end_date,
    img_dict,
    anomaly_range_stats,
    anomaly_window,
    granularity,
    oracle_insertion_id,
    time_granularity,
):
    """Build body and subject."""
    mail_kpi = kpi.mail_kpi
    # s_geo_gran = (
    #    f'{geo_granularity} ' if geo_granularity == PROVINCIAL_GEO_GRANULARITY else ''
    # )
    s_time_gran = (
        "Diarias" if time_granularity == DAILY_TIME_GRANULARITY else "Horarias"
    )
    start_anomaly_window = end_date - timedelta(days=(anomaly_window - 1))
    end_date_str = f"{end_date:%d-%b}"
    end_date_hr = (
        f"{end_date:%H} hs" if time_granularity == HOURLY_TIME_GRANULARITY else ""
    )
    # subject = (
    #     f"{anomaly_range_stats.get('nr_anomalies')} Anomalías {s_time_gran} "
    #     f"en {mail_kpi.title()} - Argentina {s_geo_gran}"
    #     f"{start_anomaly_window:%d-%b} al {end_date_str} {end_date_hr}"
    # )
    subject = (
        f"{anomaly_range_stats.get('nr_anomalies')} Anomalías {s_time_gran} "
        f"en {mail_kpi.title()} - {granularity}"
        f"{start_anomaly_window:%d-%b} al {end_date_str} {end_date_hr}"
    )
    logger.debug(f"Mail subject:\n {subject}")

    jparams = {
        "kpi": mail_kpi,
        "end_date": end_date_str,
        "img_dict": img_dict,
        "anomaly_range_stats": anomaly_range_stats,
        "anomaly_window": anomaly_window,
        "granularity": granularity,
        # "oracle_insertion_id": oracle_insertion_id,
        "time_granularity": time_granularity,
    }
    msg_body = getattr(MAIL_TEMPLATE, "mail_body")(**jparams)
    logger.debug(f"html mail body:\n {msg_body}")
    return subject, msg_body


def _get_mime_images(
    kpi,
    granularity,
    start_date,
    end_date,
    anomaly_range_stats,
    anomaly_window,
    forecast_df,
    time_granularity,
):
    """Extract images from local dir paths."""
    mime_img_dict = {}  # type: ignore
    mime_img_list = []  # type: ignore
    if anomaly_range_stats["nr_anomalies"] == 0:
        return mime_img_dict, mime_img_list

    # geos = forecast_df['factor_val'].unique().tolist()
    # if geo_granularity == PROVINCIAL_GEO_GRANULARITY:
    #    # Only do plots for provinces with most anomalies
    #    geos = anomaly_range_stats.get('most_anom_prov')
    factor_levels = forecast_df["factor_val"].unique().tolist()

    # Generate outlier images
    outliers_imgs = {}  # type: ignore
    for factor_val in factor_levels:
        df_forecast = forecast_df[forecast_df["factor_val"] == factor_val]
        fig = anomaly_plot(
            kpi_plot_name=kpi.anomaly_plot_ylabel,
            kpi_name=kpi.mail_kpi,
            granularity_val=factor_val,
            forecast_df=df_forecast,
            end_date=end_date,
            anomaly_window=anomaly_window,
            time_granularity=time_granularity,
        )
        # out_fval = (
        #    geo_val.replace(' ', '-')  # type: ignore
        #    if geo_val is not None
        #    else geo_val
        # )
        out_fval = factor_val
        end_date_hour = True if time_granularity == HOURLY_TIME_GRANULARITY else False
        fig_p = forecasts_fig_path(
            target_col=kpi.name,
            start_date=start_date,
            end_date=end_date,
            time_granularity=time_granularity,
            granularity=granularity,
            suffix=out_fval,
            as_posix=False,
            end_date_hour=end_date_hour,
        )
        logger.info(f"Saving figure to {fig_p}...")
        fig.savefig(fig_p, bbox_inches="tight")
        outliers_imgs[factor_val] = fig_p

    for factor_val, outliers_img in outliers_imgs.items():
        if outliers_img.is_file():
            if mime_img_dict.get("outliers", None) is None:
                mime_img_dict["outliers"] = {}
            with outliers_img.open("rb") as img_file:
                msg_image = MIMEImage(img_file.read())
                mime_img_list.append(msg_image)
            img_name = f"{kpi.name_spanish}_{outliers_img.stem}"
            msg_image.add_header("Content-Id", f"<{img_name}>")
            mime_img_dict["outliers"][factor_val] = img_name

    return mime_img_dict, mime_img_list


def _anomaly_range_statistics(outliers_data, granularity, end_date, time_granularity):
    """Compute ouptut statistics string from anomalies data."""
    df = outliers_data
    d = {"nr_anomalies": 0, "nr_anomalies_news": 0}

    if not df.empty:
        d["anomaly_dates"] = len(df[DS_COL].unique())
        d["nr_anomalies"] = len(df)
        d["pos_anomalies"] = len(df[df[f"{OUTLIER_SIGN_COL}"] == 1])
        d["neg_anomalies"] = len(df[df[f"{OUTLIER_SIGN_COL}"] == -1])
        worst_anomaly = (
            df[df[OUTLIER_VALUE_COL] == df[OUTLIER_VALUE_COL].max()][DS_COL]
            .head(1)
            .squeeze()
        )
        d["worst_anomaly"] = worst_anomaly.strftime("%Y-%b-%d")
        if time_granularity == HOURLY_TIME_GRANULARITY:
            d["worst_anomaly_hour"] = worst_anomaly.strftime("%H")

        # News
        news_start = pd.Timestamp(end_date).replace(hour=0)
        df_news = df[df[DS_COL] >= news_start]
        d["nr_anomalies_news"] = len(df_news)
        d["pos_anomalies_news"] = len(df_news[df_news[f"{OUTLIER_SIGN_COL}"] == 1])
        d["neg_anomalies_news"] = len(df_news[df_news[f"{OUTLIER_SIGN_COL}"] == -1])

        # Anomalies by factor value.
        worst_anomaly_by_factor_val = df[
            df[OUTLIER_VALUE_COL] == df[OUTLIER_VALUE_COL].max()
        ]["factor_val"]
        d["worst_anomaly_factor_val"] = worst_anomaly_by_factor_val.squeeze()
        df_by_factor = (
            df["factor_val"]
            .value_counts()
            .head(MAIL_WORST_FACTOR_VALS_NR)
            .reset_index()
        )
        d["most_anom_by_factor_val"] = df_by_factor["index"].tolist()

        # Build summary table
        pd.set_option("display.max_colwidth", -1)
        df = (
            df.groupby([DS_COL, f"{OUTLIER_SIGN_COL}"])
            .agg({"factor_val": lambda x: ", ".join(filter(None, x))})
            .reset_index()
        )
        df = df.rename(
            columns={
                DS_COL: "Fecha",
                f"{OUTLIER_SIGN_COL}": "Impacto",
                "factor_val": granularity,
            }
        )
        # if geo_gran != PROVINCIAL_GEO_GRANULARITY:
        #    df.drop('Provincias', inplace=True, axis=1)
        str_io = io.StringIO()
        df.to_html(
            buf=str_io, classes="table table-striped", index=False, justify="center"
        )
        d["anomaly_summary"] = str_io.getvalue()  # type: ignore

    return d


def send_mail_report(
    smtp_credentials,
    mail_recipients,
    kpi,
    granularity,
    start_date,
    end_date,
    anomaly_window,
    outliers_data,
    oracle_insertion_id,
    forecast_df,
    time_granularity,
):
    """Send mail report."""
    logger.info(f"Sending email report to: {mail_recipients}")
    anomaly_range_stats = _anomaly_range_statistics(
        outliers_data, granularity, end_date, time_granularity
    )
    if time_granularity == HOURLY_TIME_GRANULARITY:
        if anomaly_range_stats["nr_anomalies_news"] == 0:
            logger.info("No anomalies found today. No need to send any alert.")
            return
    mime_img_dict, mime_img_list = _get_mime_images(
        kpi,
        granularity,
        start_date,
        end_date,
        anomaly_range_stats=anomaly_range_stats,
        anomaly_window=anomaly_window,
        forecast_df=forecast_df,
        time_granularity=time_granularity,
    )
    subject, msg_body = _build_subject_n_msg_body(
        kpi,
        end_date,
        mime_img_dict,
        anomaly_range_stats,
        anomaly_window,
        granularity,
        oracle_insertion_id,
        time_granularity,
    )

    send_mail(smtp_credentials, mail_recipients, subject, msg_body, mime_img_list)


class MailReport(AttributeHelperMixin):
    def __init__(self, mail_recipients_list, credentials):
        self.mail_recipients_list = mail_recipients_list
        self.credentials = credentials
        self.agg_forecast_df = []  # type: ignore

    def store_forecast_data(self, forecaster, factor_conf, factor_mgr):
        forecast_df = forecaster.forecast
        forecast_df["factor_val"] = factor_conf[factor_mgr.factor_col]
        self.agg_forecast_df.append(forecast_df)

    @property
    def aggregated_forecast_data(self):
        return pd.concat(self.agg_forecast_df)

    def send(
        self, kpi, time_range_conf, factor_mgr, forecaster_insertion_id, granularity
    ):
        try:
            forecast_df = self.aggregated_forecast_data
        except ValueError:
            logger.warning("No data to do mail report!")
            return

        outliers_data = forecast_df.query(
            f"{DS_COL} in @time_range_conf.anomaly_window_dates & {OUTLIER_SIGN_COL} != 0"
        )
        # oracle_insertion_id = {
        #    'oracle': v for k, v in delver_run_ids.items() if k.startswith('oracle')
        # }.get('oracle')
        send_mail_report(
            self.credentials,
            self.mail_recipients_list,
            kpi,
            granularity,
            time_range_conf.start_date,
            time_range_conf.end_date,
            time_range_conf.anomaly_window,
            outliers_data,
            forecaster_insertion_id,
            forecast_df,
            time_granularity=time_range_conf.time_granularity,
        )
