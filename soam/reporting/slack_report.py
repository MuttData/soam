# slack_report.py
"""
Slack Report
------------
Slack reporting and message formatting tools. Its a postprocess that sends the
model forecasts though the slack app.
"""
from asyncio import Future
from pathlib import Path, PosixPath
from typing import Any, Dict, Optional, Union

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

        summary_entries = []
        summary_entries.append(greeting_message)

        for _, row in prediction.iterrows():
            date = row[DS_COL].strftime('%Y-%b-%d')
            value = "{:.2f}".format(row[YHAT_COL])
            summary_entries.append(f"• *[{date}]* {value}\n")

        summary_entries.append(farewell_message)

        summary_message = "\n".join(summary_entries)  # type: ignore

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
        self, template, arguments: Dict = None, attachment: Optional[Path] = None
    ):
        """Create Slack message.

        Args:
            template: Jinja template.
            template_args (dict): Arguments to be passed to the Jinja templates .
            attachment (Path): Path to file (or image) to attach to the image.
        """
        self.template = template
        self.arguments = arguments
        self.attachment_path = None
        self._message = None
        self._attachment = None

    @property
    def message(self) -> str:
        """Message property."""
        if self._message is None:
            self._message = path_or_string(self.template)
            if self.arguments:
                self._message = self._message.format(**self.arguments)  # type:ignore
            return self._message  # type:ignore
        else:
            return self._message

    @property
    def attachment(self) -> Optional[PosixPath]:
        """Message property."""
        if self.attachment_path is None:
            return None
        if self._attachment is None:
            if not self.attachment_path.exists():
                raise ValueError(
                    f"File does not exist: {str(self.attachment_path.resolve())}."
                )
            self._attachment = self.attachment_path.resolve()
            return self._attachment
        else:
            return self._attachment


def send_slack_message(
    channel: str, msg: SlackMessage, thread_ts: Optional[int] = None
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
    pass
