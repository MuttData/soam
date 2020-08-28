# slack_report.py
"""
SlackReport
----------
Slack reporting and message formatting tools.
"""

from pathlib import Path
from typing import Union

import pandas as pd
from soam.cfg import get_slack_cred
from soam.constants import FORECAST_DATE, YHAT_COL

import slack

DEFAULT_GREETING_MESSAGE = "Hello everyone! Here are the results of the forecast for the *{metric_name}* metric:\n"
DEFAULT_FAREWELL_MESSAGE = "Cheers!\n SoaM."


class SlackReport:
    def __init__(self, channel_id: str, metric_name: str):
        credentials = get_slack_cred()
        self.slack_client = slack.WebClient(credentials["token"])
        self.channel_id = channel_id
        self.metric_name = metric_name

    def send_report(
        self,
        prediction: pd.DataFrame,
        plot_filename: Union[str, Path],
        greeting_message: str = DEFAULT_GREETING_MESSAGE,
        farewell_message: str = DEFAULT_FAREWELL_MESSAGE,
    ):
        if greeting_message == DEFAULT_GREETING_MESSAGE:
            greeting_message.format(metric_name=self.metric_name)

        summary_entries = []
        summary_entries.append(greeting_message)

        for index, row in prediction.iterrows():
            date = row[FORECAST_DATE].strftime('%Y-%b-%d')
            value = "{:.2f}".format(row[YHAT_COL])
            summary_entries.append(f"• *[{date}]* {value}\n")

        summary_entries.append(farewell_message)

        summary_message = "\n".join(summary_entries)

        self.slack_client.files_upload(
            channels=self.channel_id,
            file=str(plot_filename),
            initial_comment=summary_message,
            title=f"{self.metric_name} Forecast",
        )
