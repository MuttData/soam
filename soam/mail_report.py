# mail_report.py
"""Mail creator and sender."""
from datetime import timedelta
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import io
import logging
from os.path import basename
import smtplib

import pandas as pd

from soam.cfg import MAIL_TEMPLATE
from soam.constants import (
    DAILY_TIME_GRANULARITY,
    DS_COL,
    HOURLY_TIME_GRANULARITY,
    PARENT_LOGGER,
)
from soam.forecast_plotter import anomaly_plot, plot_area_metrics
from soam.forecaster import (
    OUTLIER_SIGN_COL,
    OUTLIER_VALUE_COL,
    Y_COL,
    YHAT_LOWER_COL,
    YHAT_UPPER_COL,
    forecasts_fig_path,
)
from soam.helpers import AttributeHelperMixin
from soam.slack_bot import IssueReporter

logger = logging.getLogger(f'{PARENT_LOGGER}.{__name__}')


def send_mail(
    smtp_credentials, mail_recipients, subject, mail_body, mime_image_list, attachments
):
    """Send."""
    user = smtp_credentials.get('user_address')
    password = smtp_credentials.get('password')
    from_address = smtp_credentials['mail_from']
    host = smtp_credentials['host']
    port = smtp_credentials['port']
    logger.info(
        f"""About to send the following email:
                'From: ' {from_address}
                'To: ' {mail_recipients}
                'Subject: ' {subject}
                'Using host': {host} and port: {port}"""
    )
    logger.error(f'With the following body: \n {mail_body}')

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

    for attachment in attachments:
        with open(attachment, "rb") as f:
            part = MIMEApplication(f.read(), Name=basename(attachment))
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(attachment)
        msg_root.attach(part)

    with smtplib.SMTP(host, port) as server:
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
    time_granularity,
):
    """Build body and subject."""
    mail_kpi = kpi.mail_kpi

    s_time_gran = 'Daily' if time_granularity == DAILY_TIME_GRANULARITY else 'Hourly'
    end_date_str = f'{end_date:%d-%b}'
    end_date_hr = (
        f'{end_date:%H} hs' if time_granularity == HOURLY_TIME_GRANULARITY else ''
    )
    subject = (
        f"TEST - {anomaly_range_stats.get('nr_anomalies')} {s_time_gran} Anomalies "
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
    factor_mgr,
    start_date,
    end_date,
    anomaly_range_stats,
    anomaly_window,
    forecast_df,
    time_granularity,
    extra_info,
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
        fig.savefig(fig_p, bbox_inches='tight')
        outliers_imgs[factor_val] = fig_p

        # Extra plot
        if extra_info is not None:
            if extra_imgs.get(factor_val, None) is None:
                extra_imgs[factor_val] = []
            for key in extra_info.keys():
                logger.info(f'Creating extra plot for {key}')
                ex_fig = plot_area_metrics(
                    extra_info[key], factor_mgr.factor_col, factor_val
                )
                if ex_fig is None:
                    logger.warning(
                        f'Skipping {factor_val} for {key} because it has no data'
                    )
                    continue

                ex_fig_p = forecasts_fig_path(
                    target_col=kpi.name,
                    start_date=start_date,
                    end_date=end_date,
                    time_granularity=time_granularity,
                    granularity=granularity,
                    suffix=f"{out_fval}_{key}_extra",
                    as_posix=False,
                    end_date_hour=end_date_hour,
                )

                logger.info(f"Saving extra figure to {ex_fig_p}...")
                ex_fig.savefig(ex_fig_p, bbox_inches='tight')
                extra_imgs[factor_val].append(ex_fig_p)

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
            if extra_imgs.get(factor_val, None) is not None:
                mime_img_dict['extra'][factor_val] = []
                for extra_img in extra_imgs[factor_val]:
                    with extra_img.open('rb') as img_file:
                        msg_image = MIMEImage(img_file.read())
                        mime_img_list.append(msg_image)
                    img_name = f'{kpi.name_spanish}_{extra_img.stem}'
                    msg_image.add_header('Content-Id', f'<{img_name}>')
                    mime_img_dict['extra'][factor_val].append(img_name)

    return mime_img_dict, mime_img_list


def _format_link(factor):
    return f'<a href=#{factor}>{factor}</a>'


def _format_factor_val(row):
    if row[OUTLIER_SIGN_COL] == 1:
        relative_gap = _relative_gap(row)
        return (
            f'<a href=#{row["factor_val"]}>{row["factor_val"]}</a> was {relative_gap}'
        )
    else:
        relative_gap = _relative_gap(row)
        return (
            f'<a href=#{row["factor_val"]}>{row["factor_val"]}</a> was {relative_gap}'
        )


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

        # Build summary table
        pd.set_option('display.max_colwidth', -1)
        df['factor_val_original'] = df['factor_val']
        df['factor_val'] = df.apply(_format_factor_val, axis=1)
        df = (
            df.groupby([DS_COL, f'{OUTLIER_SIGN_COL}'])
            .agg({'factor_val': lambda x: ', '.join(x)})
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
            buf=str_io,
            classes='table table-striped',
            index=False,
            justify='center',
            escape=False,
        )
        d['anomaly_summary'] = str_io.getvalue()  # type: ignore

    return d


def _relative_gap(row):
    if row[OUTLIER_SIGN_COL] == 1:
        relative_gap = (row[Y_COL] - row[YHAT_UPPER_COL]) / row[YHAT_UPPER_COL] * 100
        return f"{round(relative_gap,2)}% higher"
    else:
        relative_gap = -(row[Y_COL] - row[YHAT_LOWER_COL]) / row[YHAT_LOWER_COL] * 100
        return f"{round(relative_gap,2)}% lower"


def send_mail_report(
    smtp_credentials,
    mail_recipients,
    kpi,
    granularity,
    factor_mgr,
    start_date,
    end_date,
    anomaly_window,
    outliers_data,
    forecast_df,
    time_granularity,
    extra_info=None,
    email_attachments=None,
    slack_settings=None,
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
        factor_mgr,
        start_date,
        end_date,
        anomaly_range_stats=anomaly_range_stats,
        anomaly_window=anomaly_window,
        forecast_df=forecast_df,
        time_granularity=time_granularity,
        extra_info=extra_info,
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

    if slack_settings:
        slack_reporter = IssueReporter(slack_settings['token'])
        slack_anomalies = []
        for index, row in outliers_data.iterrows():
            print(row)
            slack_anomalies.append(
                {
                    'factor_val': row['factor_val_original'],
                    'kpi': kpi.name,
                    'metric': _relative_gap(row),
                    'date': row[DS_COL].strftime("%B %d"),
                    'picture': str(
                        forecasts_fig_path(
                            target_col=kpi.name,
                            start_date=start_date,
                            end_date=end_date,
                            time_granularity=time_granularity,
                            granularity=granularity,
                            suffix=row['factor_val_original'],
                            as_posix=False,
                            end_date_hour=False,
                        )
                    ),
                }
            )

        if len(slack_anomalies) > 0:
            slack_reporter.send_report(slack_anomalies, slack_settings['channel'])

    send_mail(
        smtp_credentials,
        mail_recipients,
        subject,
        msg_body,
        mime_img_list,
        email_attachments,
    )


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
        factor_mgr,
        time_range_conf,
        forecaster_insertion_id,
        extra_info,
        email_attachments,
        slack_settings,
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
            factor_mgr,
            time_range_conf.start_date,
            time_range_conf.end_date,
            time_range_conf.anomaly_window,
            outliers_data,
            forecast_df,
            time_granularity=time_range_conf.time_granularity,
            extra_info=extra_info,
            email_attachments=email_attachments,
            slack_settings=slack_settings,
        )
