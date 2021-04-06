# slack_report.py
"""
Slack Report
------------
Slack reporting and message formatting tools. Its a postprocess that sends the
model forecasts though the slack app.
"""
from asyncio import Future
from pathlib import Path
from typing import Any, Optional, Union

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
