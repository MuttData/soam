# mail_report.py
"""Mail creator and sender."""
import io
import logging
import smtplib
from datetime import timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import matplotlib.pyplot as plt

import pandas as pd

from soam.cfg import MAIL_TEMPLATE
from soam.constants import (
    DAILY_TIME_GRANULARITY,
    DS_COL,
    HOURLY_TIME_GRANULARITY,
    PARENT_LOGGER,
)
from soam.forecaster import OUTLIER_SIGN_COL, OUTLIER_VALUE_COL, forecasts_fig_path
from soam.helpers import AttributeHelperMixin
from soam.forecast_plotter import anomaly_plot

logger = logging.getLogger(f'{PARENT_LOGGER}.{__name__}')


def send_mail(smtp_credentials, mail_recipients, subject, mail_body, mime_image_list):
    """Send."""
    user = smtp_credentials.get('user_address')
    password = smtp_credentials.get('password')
    from_address = smtp_credentials['mail_from']
    msg_root = MIMEMultipart('related')
    msg_root['From'] = from_address
    msg_root['Subject'] = subject
    msg_root['To'] = ', '.join(mail_recipients)

    msg_alt = MIMEMultipart('alternative')
    msg_root.attach(msg_alt)

    msg_text = MIMEText(mail_body, 'html')
    msg_alt.attach(msg_text)

    for mim_img in mime_image_list:
        msg_root.attach(mim_img)

    user = smtp_credentials.get('user_address')
    password = smtp_credentials.get('password')
    with smtplib.SMTP(smtp_credentials['host'], smtp_credentials['port']) as server:
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
    # geo_granularity,
    granularity,
    time_granularity,
):
    """Build body and subject."""
    mail_kpi = kpi.mail_kpi

    s_time_gran = 'Daily' if time_granularity == DAILY_TIME_GRANULARITY else 'Hourly'
    start_anomaly_window = end_date - timedelta(days=(anomaly_window - 1))
    end_date_str = f'{end_date:%d-%b}'
    end_date_hr = (
        f'{end_date:%H} hs' if time_granularity == HOURLY_TIME_GRANULARITY else ''
    )
    subject = (
        f"{anomaly_range_stats.get('nr_anomalies')} {s_time_gran} Anomalies "
        f"detected in {mail_kpi} "
        f"{end_date_str} {end_date_hr}"
    )
    logger.debug(f"Mail subject:\n {subject}")

    jparams = {
        'kpi': mail_kpi,
        'end_date': end_date_str,
        'img_dict': img_dict,
        'anomaly_range_stats': anomaly_range_stats,
        'anomaly_window': anomaly_window,
        'granularity': granularity,
        'time_granularity': time_granularity,
    }
    msg_body = getattr(MAIL_TEMPLATE, 'mail_body')(**jparams)
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
    orig_df,
):
    """Extract images from local dir paths."""
    mime_img_dict = {}  # type: ignore
    mime_img_list = []  # type: ignore
    if anomaly_range_stats['nr_anomalies'] == 0:
        return mime_img_dict, mime_img_list

    factor_levels = forecast_df['factor_val'].unique().tolist()
    logger.info(f"FACTOR LEVELS: {factor_levels}")

    # Generate outlier images
    outliers_imgs = {}  # type: ignore

    # Generate extra images
    extra_imgs = {}  # type: ignore

    for factor_val in factor_levels:
        df_forecast = forecast_df[forecast_df['factor_val'] == factor_val]
        # Anomaly plot
        fig = anomaly_plot(
            kpi_plot_name=kpi.anomaly_plot_ylabel,
            kpi_name=kpi.mail_kpi,
            granularity_val=factor_val,
            forecast_df=df_forecast,
            end_date=end_date,
            anomaly_window=anomaly_window,
            time_granularity=time_granularity,
        )
        # Extra plot
        pdf = orig_df[orig_df["game"] == factor_val]
        pdf = pdf.groupby(['date', 'provider']).sum().reset_index()
        pdf['date'] = pd.to_datetime(pdf['date'])
        ex_fig = plot_provider_area_metrics(
            pdf, ['cache_requests', 'cache_successes', 'view_requests', 'view_starts']
        )

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
        ex_fig_p = forecasts_fig_path(
            target_col=kpi.name,
            start_date=start_date,
            end_date=end_date,
            time_granularity=time_granularity,
            granularity=granularity,
            suffix=f"{out_fval}_extra",
            as_posix=False,
            end_date_hour=end_date_hour,
        )

        logger.info(f"Saving figure to {fig_p}...")
        fig.savefig(fig_p, bbox_inches='tight')
        logger.info(f"Saving extra figure to {ex_fig_p}...")
        ex_fig.savefig(ex_fig_p, bbox_inches='tight')
        outliers_imgs[factor_val] = fig_p
        extra_imgs[factor_val] = ex_fig_p

    for factor_val, outliers_img in outliers_imgs.items():
        if outliers_img.is_file():
            if mime_img_dict.get('outliers', None) is None:
                mime_img_dict['outliers'] = {}
                mime_img_dict['extra'] = {}
            with outliers_img.open('rb') as img_file:
                msg_image = MIMEImage(img_file.read())
                mime_img_list.append(msg_image)
            img_name = f'{kpi.name_spanish}_{outliers_img.stem}'
            msg_image.add_header('Content-Id', f'<{img_name}>')
            mime_img_dict['outliers'][factor_val] = img_name
            if extra_imgs[factor_val]:
                extra_img = extra_imgs[factor_val]
                with extra_img.open('rb') as img_file:
                    msg_image = MIMEImage(img_file.read())
                    mime_img_list.append(msg_image)
                img_name = f'{kpi.name_spanish}_{extra_img.stem}'
                msg_image.add_header('Content-Id', f'<{img_name}>')
                mime_img_dict['extra'][factor_val] = img_name

    return mime_img_dict, mime_img_list


def plot_provider_area_metrics(pdf, metrics):
    if len(pdf) == 0:
        print('Empty dataframe')
    else:
        fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(50, 25))
        pos = [[0, 0], [0, 1], [1, 0], [1, 1]]
        for i, m in enumerate(metrics):
            df = pdf.copy()
            fig_bar = (
                df.sort_values(['date', 'provider'])
                .set_index(['date', 'provider'])[m]
                .unstack()
                .plot(
                    kind='area',
                    stacked=True,
                    figsize=(12, 7),
                    colormap='Spectral',
                    rot=45,
                    fontsize=6,
                    ax=axes[pos[i][0], pos[i][1]],
                )
            )
            fig_bar.legend(loc='upper left', bbox_to_anchor=(1, 1), prop={'size': 6})
            fig_bar.set_title(f'{m} by provider')
        fig.tight_layout(pad=2.0)
        return fig


def _anomaly_range_statistics(outliers_data, granularity, end_date, time_granularity):
    """Compute ouptut statistics string from anomalies data."""
    df = outliers_data
    d = {'nr_anomalies': 0, 'nr_anomalies_news': 0}

    if not df.empty:
        d['anomaly_dates'] = len(df[DS_COL].unique())
        d['nr_anomalies'] = len(df)
        d['pos_anomalies'] = len(df[df[f'{OUTLIER_SIGN_COL}'] == 1])
        d['neg_anomalies'] = len(df[df[f'{OUTLIER_SIGN_COL}'] == -1])
        worst_anomaly = (
            df[df[OUTLIER_VALUE_COL] == df[OUTLIER_VALUE_COL].max()][DS_COL]
            .head(1)
            .squeeze()
        )
        d['worst_anomaly'] = worst_anomaly.strftime('%Y-%b-%d')
        if time_granularity == HOURLY_TIME_GRANULARITY:
            d['worst_anomaly_hour'] = worst_anomaly.strftime('%H')

        # News
        news_start = pd.Timestamp(end_date).replace(hour=0)
        df_news = df[df[DS_COL] >= news_start]
        d['nr_anomalies_news'] = len(df_news)
        d['pos_anomalies_news'] = len(df_news[df_news[f'{OUTLIER_SIGN_COL}'] == 1])
        d['neg_anomalies_news'] = len(df_news[df_news[f'{OUTLIER_SIGN_COL}'] == -1])

        if (
            False
        ):  # This part should be it's a trivial factorization: len(factor_levels) > 1
            worst_anomaly_prov = df[
                df[OUTLIER_VALUE_COL] == df[OUTLIER_VALUE_COL].max()
            ]['factor_val']
            d['worst_anomaly_factor_val'] = worst_anomaly_prov.squeeze()
            df_prov = (
                df['factor_val']
                .value_counts()
                .head(MAIL_WORST_PROVINCES_NR)
                .reset_index()
            )
            d['most_anom_factor '] = df_prov['index'].tolist()

        # Build summary table
        pd.set_option('display.max_colwidth', -1)
        df = (
            df.groupby([DS_COL, f'{OUTLIER_SIGN_COL}'])
            .agg({'factor_val': lambda x: ', '.join(filter(None, x))})
            .reset_index()
        )
        df = df.rename(
            columns={
                DS_COL: 'Date',
                f'{OUTLIER_SIGN_COL}': 'Impact',
                'factor_val': 'Game',
            }
        )

        str_io = io.StringIO()
        df.to_html(
            buf=str_io, classes='table table-striped', index=False, justify='center'
        )
        d['anomaly_summary'] = str_io.getvalue()  # type: ignore

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
    forecast_df,
    time_granularity,
    orig_df=None,
):
    """Send mail report."""
    logger.info(f"Sending email report to: {mail_recipients}")
    anomaly_range_stats = _anomaly_range_statistics(
        outliers_data, granularity, end_date, time_granularity
    )
    if time_granularity == HOURLY_TIME_GRANULARITY:
        if anomaly_range_stats['nr_anomalies_news'] == 0:
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
        orig_df=orig_df,
    )
    subject, msg_body = _build_subject_n_msg_body(
        kpi,
        end_date,
        mime_img_dict,
        anomaly_range_stats,
        anomaly_window,
        granularity,
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
        forecast_df['factor_val'] = factor_conf[factor_mgr.factor_col]
        self.agg_forecast_df.append(forecast_df)

    @property
    def aggregated_forecast_data(self):
        return pd.concat(self.agg_forecast_df)

    def send(
        self,
        kpi,
        granularity,
        time_range_conf,
        factor_mgr,
        forecaster_insertion_id,
        orig_df,
    ):
        try:
            forecast_df = self.aggregated_forecast_data
        except ValueError:
            logger.warning("No data to do mail report!")
            return

        outliers_data = forecast_df.query(
            f'{DS_COL} in @time_range_conf.anomaly_window_dates & {OUTLIER_SIGN_COL} != 0'
        )

        send_mail_report(
            self.credentials,
            self.mail_recipients_list,
            kpi,
            granularity,
            time_range_conf.start_date,
            time_range_conf.end_date,
            time_range_conf.anomaly_window,
            outliers_data,
            forecast_df,
            time_granularity=time_range_conf.time_granularity,
            orig_df=orig_df,
        )
