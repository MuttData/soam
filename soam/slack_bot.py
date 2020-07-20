import logging

import slack
from soam.constants import PARENT_LOGGER

logger = logging.getLogger(f'{PARENT_LOGGER}.{__name__}')


class IssueReporter:
    """Class in charge of sending the issue report."""

    def __init__(self, slack_token):
        """Construct IssueReporter with necessary clients."""
        self.slack_client = slack.WebClient(slack_token)

    def send_report(self, anomalies, channel_id):
        pictures = []
        summary_entries = []

        # Build anomaly summary
        for anomaly in anomalies:
            factor = anomaly['factor_val']
            kpi = anomaly['kpi']
            metric = anomaly['metric']
            date = anomaly['date']
            picture_file = anomaly['picture']

            summary_entries.append(
                f"• *{factor}*'s {kpi} was *{metric}* than expected for {date}"
            )

            pictures.append({'factor': factor, 'filename': picture_file})

        # Send summary
        summary_message = "\n".join(summary_entries)
        response = self.slack_client.chat_postMessage(
            channel=channel_id, text=summary_message
        )

        message_timestamp = response.get('ts')

        # Send pictures to the thread
        logging.info("Starting with pics")
        print("PICS!!")
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
