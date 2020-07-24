import logging

import pandas as pd

import slack
from soam.constants import PARENT_LOGGER

logger = logging.getLogger(f'{PARENT_LOGGER}.{__name__}')


def _relative_gap_expected(value, expected_value):
    relative_gap = (value - expected_value) / expected_value * 100
    return round(relative_gap, 2)


class IssueReporter:
    """Class in charge of sending the issue report."""

    def __init__(self, slack_token):
        """Construct IssueReporter with necessary clients."""
        self.slack_client = slack.WebClient(slack_token)

    def send_report(self, anomalies, channel_id, email_attachments, kpi, run_date):
        pictures = []
        summary_entries = []
        run_date = pd.to_datetime(run_date, format='%Y-%m-%d %H:%M')
        # Build anomaly summary
        for anomaly_date in anomalies.keys():
            if run_date.hour > 12:
                summary_entries.append(
                    f"*[Afternoon Check for {run_date.year}-{run_date.month:02}-{run_date.day}]*"
                )
            else:
                summary_entries.append(
                    f"*[Morning Check for {run_date.year}-{run_date.month:02}-{run_date.day}]* - please note that this may contain incomplete {kpi} data"
                )
            summary_entries.append(
                f"Hello everyone! {len(anomalies[anomaly_date])} anomalies have been detected for the *{kpi}* metric:\n"
            )
            for anomaly in anomalies[anomaly_date]:
                factor = anomaly['factor_val']
                kpi = anomaly['kpi']
                metric = anomaly['metric']
                expected_metric = anomaly['expected_metric']
                lower_boundary = anomaly['lower_boundary']

                relative_gap = _relative_gap_expected(metric, expected_metric)
                lower_boundary_gap = -_relative_gap_expected(
                    lower_boundary, expected_metric
                )

                picture_file = anomaly['picture']

                summary_entries.append(
                    f"• *{factor}*'s {kpi} was *{-relative_gap}% lower* than expected [we expected *${round(expected_metric,2)}* (with a lower bound *{lower_boundary_gap}% lower* than the expected {kpi}) and we got *${round(metric,2)}* ({-relative_gap}% lower than the expected {kpi})]"
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
