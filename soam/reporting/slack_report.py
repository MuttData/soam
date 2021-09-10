# slack_report.py
"""
Slack Report
------------
Slack reporting and message formatting tools. Its a postprocess that sends the
model forecasts though the slack app.
"""
from asyncio import Future
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path, PosixPath
from typing import IO, Any, Dict, Optional, Sequence, Union
import warnings

from jinja2 import Template
from muttlib.utils import path_or_string
import pandas as pd
import slack
from slack.web.slack_response import SlackResponse

from soam.cfg import get_slack_cred
from soam.constants import DS_COL, YHAT_COL
from soam.core.step import Step

DEFAULT_GREETING_MESSAGE = "Hello everyone! Here are the results of the forecast for the *{metric_name}* metric:\n"
DEFAULT_FAREWELL_MESSAGE = "Cheers!\n SoaM."


class SlackReport:
    """
    Generates the report to share via Slack.
    """

    warnings.warn(
        "This class will be deprecated in v1. Using SlackMessage and send_slack_message methods instead is recommended.",
        PendingDeprecationWarning,
    )

    def __init__(
        self, channel_id: str, metric_name: str, setting_path: Optional[str],
    ):
        """
        Initialization of the Slack Report object.

        Parameters
        ----------
        channel_id: str
            Slack channel id where the report will be sent.
        metric_name: str
            Performance metric being measured.
        setting_path: str
            Setting path.
        """
        credentials = get_slack_cred(setting_path)
        self.slack_client = slack.WebClient(credentials["token"])
        self.channel_id = channel_id
        self.metric_name = metric_name

    def send_report(
        self,
        prediction: pd.DataFrame,
        plot_filename: Union[str, Path],
        greeting_message: Optional[str] = DEFAULT_GREETING_MESSAGE,
        farewell_message: Optional[str] = DEFAULT_FAREWELL_MESSAGE,
    ) -> Union[Future, SlackResponse]:
        """
        Send Slack report.

        Parameters
        ----------
        prediction : pd.DataFrame
            DataDrame of the predictions made.
        plot_filename : str or pathlib.Path
             Path of the forecast data to send.
        greeting_message: str
            Greeting message to send via Slack with the predictions.
        farewell_message: str
            Farewell message to send via Slack with the predictions.

        Returns
        -------
        Slack Report
            Sends the specified message with the predictions data via Slack.
        """
        if greeting_message == DEFAULT_GREETING_MESSAGE:
            greeting_message.format(metric_name=self.metric_name)

        prediction[f"{YHAT_COL}_str"] = prediction[YHAT_COL].apply(
            lambda f: "{:.2f}".format(f)  # pylint: disable=unnecessary-lambda
        )
        summary_message = _df_to_report_string(
            prediction,
            DS_COL,
            f"{YHAT_COL}_str",
            greeting_message=greeting_message,
            farewell_message=farewell_message,
        )
        prediction = prediction.drop(columns=[f"{YHAT_COL}_str"])

        return self.slack_client.files_upload(
            channels=self.channel_id,
            file=str(plot_filename),
            initial_comment=summary_message,
            title=f"{self.metric_name} Forecast",
        )


class SlackReportTask(Step, SlackReport):
    """
    Builds up the task of the report designed for Slack.
    """

    warnings.warn(
        "This class will be deprecated in v1. Using SlackMessage and send_slack_message methods instead is recommended.",
        PendingDeprecationWarning,
    )

    def __init__(
        self,
        channel_id: str,
        metric_name: str,
        setting_path: Optional[str],
        **kwargs: Any,
    ):
        """
        Parameters
        ----------
        channel_id: str
            Slack channel id where the report will be sent.
        metric_name: str
            Performance metric being measured.
        setting_path: str
            Setting path.
        kwargs:
            Extra args to pass.
        """
        Step.__init__(self, **kwargs)  # type: ignore
        SlackReport.__init__(
            self, channel_id, metric_name, setting_path,
        )

    def run(  # type: ignore
        self,
        prediction: pd.DataFrame,
        plot_filename: Union[str, Path],
        greeting_message: Optional[str] = DEFAULT_GREETING_MESSAGE,
        farewell_message: Optional[str] = DEFAULT_FAREWELL_MESSAGE,
    ):
        """
        Send Slack report task.

        Parameters
        ----------
        prediction : pd.DataFrame
            DataDrame of the predictions made.
        plot_filename : str or pathlib.Path
             Path of the forecast data to send.
        greeting_message: str
            Greeting message to send via Slack with the predictions.
        farewell_message: str
            Farewell message to send via Slack with the predictions.

        Returns
        -------
        Slack Report Task
            Sends the specified message with the predictions data via Slack.
        """
        return self.send_report(
            prediction, plot_filename, greeting_message, farewell_message
        )


class SlackMessage:
    def __init__(
        self,
        template,
        arguments: Dict = None,
        attachment: Optional[Union[Path, IO]] = None,
    ):
        """Create Slack message.

        Args:
            template: Jinja template.
            template_args (dict): Arguments to be passed to the Jinja templates .
            attachment (Path): Path to file (or image) to attach to the image.
        """
        self.template = template
        self.arguments = arguments
        self.attachment_ref = attachment

    @property
    def message(self) -> str:
        """Message property."""
        message = path_or_string(self.template)
        if self.arguments:
            template = Template(message)
            message = template.render(**self.arguments)  # type:ignore
        return message

    @property
    def attachment(self) -> Optional[Union[str, IO]]:
        """Message property."""
        if self.attachment_ref is None:
            return None
        if isinstance(self.attachment_ref, PosixPath):
            if not self.attachment_ref.exists():
                raise ValueError(
                    f"File does not exist: {str(self.attachment_ref.resolve())}."
                )
            # slack's client supports a string with the path for the file
            return str(self.attachment_ref.resolve())
        elif isinstance(self.attachment_ref, BytesIO):
            return self.attachment_ref
        else:
            raise TypeError("Only PosixPath and BytesIO supported.")


def send_slack_message(
    slack_client: slack.WebClient,
    channel: str,
    msg: SlackMessage,
    thread_ts: Optional[int] = None,
):
    """Send Slack message.

    Parameters
    ----------
    channel : str
        slack channel to send the message to.
    msg : SlackMessage
        SlackMessage instance.
    thread_ts : int, optional
        message timestamp to reply to in threaded fashion, by default None.
    """
    if msg.attachment is None:
        response = slack_client.chat_postMessage(
            channel=channel, text=msg.message, thread_ts=thread_ts
        )
    else:
        response = slack_client.files_upload(
            file=msg.attachment,
            channels=channel,
            initial_comment=msg.message,
            thread_ts=thread_ts,
        )
    return response


def send_slack_messages_in_thread(
    slack_client: slack.WebClient, channel: str, messages: Sequence[SlackMessage]
):
    first_message = messages[0]
    response = send_slack_message(slack_client, channel, first_message)
    for msg in messages[1:]:
        response = send_slack_message(
            slack_client, channel, msg, thread_ts=response["ts"]
        )


def send_multiple_slack_messages(
    slack_client: slack.WebClient,
    channel: str,
    messages: Sequence[Union[SlackMessage, Sequence[SlackMessage]]],
):
    for element in messages:
        if isinstance(element, Iterable):
            send_slack_messages_in_thread(slack_client, channel, element)
        else:
            send_slack_message(slack_client, channel, element)


def _format_number(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'k', 'M', 'G', 'T', 'P'][magnitude])


def _df_to_report_string(
    df, date_col, value_col, greeting_message=None, farewell_message=None
):
    """Concatenates the rows using the date_col and value_col for formatting purposes."""
    summary_entries = []
    if greeting_message:
        summary_entries.append(greeting_message)

    for _, row in df.iterrows():
        date = row[date_col].strftime('%Y-%b-%d')
        value = row[value_col]
        summary_entries.append(f"• *[{date}]* {value}\n")

    if farewell_message:
        summary_entries.append(farewell_message)

    summary_message = "\n".join(summary_entries)  # type: ignore
    return summary_message


def send_anomaly_report(
    slack_client: slack.WebClient,
    channel_id: str,
    plot: Union[Path, IO],
    metric_name: str,
    anomaly_df: pd.DataFrame,
    date_col: str,
):
    """
    Parameters
    ----------
    channel_id: str
        Slack channel id where the report will be sent.
    plot: str, pathlib.Path or buffer
        Anomaly plot
    metric_name: str
        Metric to report.
    anomaly_df: pd.DataFrame
        DataFrame with anomalous values. Must have the following columns: ['y','yhat','yhat_lower','yhat_upper']
    date_col: str
        Name of the date column
    """
    detection_window = len(anomaly_df)
    stddev = anomaly_df.yhat.std()
    anomaly_df['stddev'] = abs(anomaly_df.yhat - anomaly_df.y) / stddev
    anomaly_df['anomaly_upper'] = anomaly_df['y'] > anomaly_df['yhat_upper']
    anomaly_df['anomaly_lower'] = anomaly_df['y'] < anomaly_df['yhat_lower']
    aux = anomaly_df.loc[(anomaly_df['anomaly_lower']) | (anomaly_df['anomaly_upper'])]
    if len(aux) == 0:
        greeting_message = "Hello everyone! Good news: there were no outliers found for the last {{detection_window}} days for the metric '{{metric_name}}'"
        msg = SlackMessage(
            greeting_message,
            arguments={
                "detection_window": detection_window,
                "metric_name": metric_name,
            },
            attachment=plot,
        )
    else:
        aux['message'] = aux.apply(
            lambda row: f"Count: {_format_number(row['y'])}, expected value in range ( {_format_number(row['yhat_lower'])} , {_format_number(row['yhat_upper'])} ) - {row['stddev']:.2f} standard deviations",
            axis=1,
        )
        greeting_message = f"Hello everyone! Here are the outliers found for the last {detection_window} days for the metric '{metric_name}'"
        summary_message = _df_to_report_string(
            aux,
            date_col,
            'message',
            greeting_message=greeting_message,
            farewell_message=None,
        )
        msg = SlackMessage(summary_message, attachment=plot)

    send_slack_message(slack_client, channel=channel_id, msg=msg)
