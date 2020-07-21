import logging

import pandas as pd

import slack
from soam.constants import PARENT_LOGGER

logger = logging.getLogger(f'{PARENT_LOGGER}.{__name__}')


class IssueReporter:
    """Class in charge of sending the issue report."""

    def __init__(self, slack_token):
        """Construct IssueReporter with necessary clients."""
        self.slack_client = slack.WebClient(slack_token)

    def send_report(self, anomalies, channel_id, email_attachments, kpi):
        pictures = []
        summary_entries = []

        summary_entries.append(
            f"Hello Everyone! There have been {len(anomalies.keys())} anomalies for the *{kpi}* metric for the last two days:\n"
        )

        # Build anomaly summary
        for anomaly_date in anomalies.keys():
            date = pd.to_datetime(str(anomaly_date))
            summary_entries.append(f"{date.strftime('%B %d')}\n\n")
            for anomaly in anomalies[anomaly_date]:
                factor = anomaly['factor_val']
                kpi = anomaly['kpi']
                metric = anomaly['metric']
                picture_file = anomaly['picture']

                summary_entries.append(
                    f"• *{factor}*'s {kpi} was *{metric}* than expected"
                )

                if picture_file:
                    pictures.append({'factor': factor, 'filename': picture_file})
            summary_entries.append("\n")

        summary_entries.append("Cheers!\n")

        # Send summary
        summary_message = "\n".join(summary_entries)
        response = self.slack_client.chat_postMessage(
            channel=channel_id, text=summary_message
        )

        message_timestamp = response.get('ts')

        # Send pictures to the thread
        for picture in pictures:
            logger.info(picture)
            print(picture)
            response = self.slack_client.files_upload(
                channels=channel_id,
                file=picture['filename'],
                initial_comment=f"Anomalies chart for *{picture['factor']}*",
                title=f"{picture['factor']} Anomalies",
                thread_ts=message_timestamp,
            )

        # Send attachments to the thread
        for attach in email_attachments:
            response = self.slack_client.files_upload(
                channels=channel_id,
                file=attach,
                initial_comment="Extra metrics",
                thread_ts=message_timestamp,
            )
