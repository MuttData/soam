"""Slack report test."""

from datetime import date
from io import BytesIO
from pathlib import Path, PosixPath
from unittest.mock import MagicMock

from jinja2 import Template
import pandas as pd
import pytest

from soam.reporting.slack_report import (
    SlackMessage,
    send_anomaly_report,
    send_multiple_slack_messages,
    send_slack_message,
)

SLACK_MSG_TEMPLATE = """
Hello {{ user }}, welcome to SOAM {{ version }}"""


def test_slack_message_object_with_path(tmp_path):
    """Test slack message object with path as attachment."""
    temp_file = tmp_path / "mytemp.txt"
    temp_file_content = "test text"
    temp_file.write_text(temp_file_content)
    template_params = dict(user="test", version="0.1.0")
    slack_msg = SlackMessage(
        SLACK_MSG_TEMPLATE, arguments=template_params, attachment=temp_file
    )
    assert slack_msg.message == Template(SLACK_MSG_TEMPLATE).render(**template_params)
    assert slack_msg.attachment == str(temp_file.resolve())
    assert Path(slack_msg.attachment).read_text() == temp_file_content


def test_slack_message_object_with_file():
    """Test slack message object with buffer as attachment."""
    byte_file = BytesIO(b"abcdef")
    template_params = dict(user="test", version="0.1.0")
    slack_msg = SlackMessage(
        SLACK_MSG_TEMPLATE, arguments=template_params, attachment=byte_file
    )
    assert slack_msg.message == Template(SLACK_MSG_TEMPLATE).render(**template_params)
    assert slack_msg.attachment == byte_file


def test_send_slack_message_no_attachment():
    client_mock = MagicMock()
    template_params = dict(user="test", version="0.1.0")
    slack_msg = SlackMessage(SLACK_MSG_TEMPLATE, arguments=template_params)
    test_channel = "test"
    send_slack_message(slack_client=client_mock, channel=test_channel, msg=slack_msg)
    client_mock.chat_postMessage.assert_called_once_with(
        channel=test_channel, text=slack_msg.message, thread_ts=None
    )


def test_send_slack_message_with_path_attachment(tmp_path):
    client_mock = MagicMock()
    temp_file = tmp_path / "mytemp.txt"
    temp_file_content = "test text"
    temp_file.write_text(temp_file_content)
    template_params = dict(user="test", version="0.1.0")
    slack_msg = SlackMessage(
        SLACK_MSG_TEMPLATE, arguments=template_params, attachment=temp_file
    )
    test_channel = "test"
    send_slack_message(slack_client=client_mock, channel=test_channel, msg=slack_msg)
    client_mock.files_upload.assert_called_once_with(
        file=slack_msg.attachment,
        channels=test_channel,
        initial_comment=slack_msg.message,
        thread_ts=None,
    )


def test_send_slack_message_with_buffer_attachment():
    client_mock = MagicMock()
    byte_file = BytesIO(b"abcdef")
    template_params = dict(user="test", version="0.1.0")
    slack_msg = SlackMessage(
        SLACK_MSG_TEMPLATE, arguments=template_params, attachment=byte_file
    )
    test_channel = "test"
    send_slack_message(slack_client=client_mock, channel=test_channel, msg=slack_msg)
    client_mock.files_upload.assert_called_once_with(
        file=byte_file,
        channels=test_channel,
        initial_comment=slack_msg.message,
        thread_ts=None,
    )


def test_slack_message_with_non_existing_attachment_fails():
    path_mock = MagicMock(spec=PosixPath)
    path_mock.exists.return_value = False
    template_params = dict(user="test", version="0.1.0")
    slack_msg = SlackMessage(
        SLACK_MSG_TEMPLATE, arguments=template_params, attachment=path_mock
    )
    with pytest.raises(ValueError):
        slack_msg.attachment  # pylint: disable=pointless-statement


def test_send_multiple_messages_to_channel():
    client_mock = MagicMock()
    byte_file = BytesIO(b"abcdef")
    template_params = dict(user="test", version="0.1.0")
    slack_msg1 = SlackMessage(
        SLACK_MSG_TEMPLATE, arguments=template_params, attachment=byte_file
    )
    slack_msg2 = SlackMessage(SLACK_MSG_TEMPLATE, arguments=template_params)
    test_channel = "test"
    send_multiple_slack_messages(
        client_mock, channel=test_channel, messages=[slack_msg1, slack_msg2]
    )
    client_mock.files_upload.assert_called_once_with(
        file=byte_file,
        channels=test_channel,
        initial_comment=slack_msg2.message,
        thread_ts=None,
    )
    client_mock.chat_postMessage.assert_called_once_with(
        channel=test_channel, text=slack_msg1.message, thread_ts=None
    )


def test_send_multiple_messages_to_channel_in_thread():
    client_mock = MagicMock()
    test_ts = "test_ts"
    client_mock.files_upload.return_value = {"ts": test_ts}
    byte_file = BytesIO(b"abcdef")
    template_params = dict(user="test", version="0.1.0")
    slack_msg1 = SlackMessage(
        SLACK_MSG_TEMPLATE, arguments=template_params, attachment=byte_file
    )
    slack_msg2 = SlackMessage(SLACK_MSG_TEMPLATE, arguments=template_params)
    test_channel = "test"
    send_multiple_slack_messages(
        client_mock, channel=test_channel, messages=[[slack_msg1, slack_msg2]]
    )
    client_mock.files_upload.assert_called_once_with(
        file=byte_file,
        channels=test_channel,
        initial_comment=slack_msg1.message,
        thread_ts=None,
    )
    client_mock.chat_postMessage.assert_called_once_with(
        channel=test_channel, text=slack_msg2.message, thread_ts=test_ts
    )


def test_send_multiple_messages_to_channel_in_thread_single():
    client_mock = MagicMock()
    test_ts = "test_ts"
    client_mock.files_upload.return_value = {"ts": test_ts}
    byte_file = BytesIO(b"abcdef")
    template_params = dict(user="test", version="0.1.0")
    slack_msg1 = SlackMessage(
        SLACK_MSG_TEMPLATE, arguments=template_params, attachment=byte_file
    )
    test_channel = "test"
    send_multiple_slack_messages(
        client_mock, channel=test_channel, messages=[[slack_msg1]]
    )
    client_mock.files_upload.assert_called_once_with(
        file=byte_file,
        channels=test_channel,
        initial_comment=slack_msg1.message,
        thread_ts=None,
    )
    client_mock.chat_postMessage.assert_not_called()


def test_send_anomaly_report():
    client_mock = MagicMock()
    plot_file = BytesIO(b"abcdef")
    anomaly_df = pd.DataFrame(
        [
            [date(2021, 1, 1), 2.5, 1.01, 2.2, 0.5],
            [date(2021, 1, 2), 4.01, 4.02, 4.7, 3.9],
        ],
        columns=["date", "y", "yhat", "yhat_upper", "yhat_lower"],
    )
    metric_name = "test"
    test_channel = "test"
    send_anomaly_report(
        client_mock, test_channel, plot_file, metric_name, anomaly_df, "date"
    )
    expected_message = "Hello everyone! Here are the outliers found for the last 2 days for the metric 'test'\n• *[2021-Jan-01]* Count: 2.50, expected value in range ( 0.50 , 2.20 ) - 0.70 standard deviations\n"
    client_mock.files_upload.assert_called_once_with(
        file=plot_file,
        channels=test_channel,
        initial_comment=expected_message,
        thread_ts=None,
    )


def test_send_no_anomaly_report():
    client_mock = MagicMock()
    plot_file = BytesIO(b"abcdef")
    anomaly_df = pd.DataFrame(
        [
            [date(2021, 1, 1), 1.5, 1.01, 2.2, 0.5],
            [date(2021, 1, 2), 4.01, 4.02, 4.7, 3.9],
        ],
        columns=["date", "y", "yhat", "yhat_upper", "yhat_lower"],
    )
    metric_name = "test"
    test_channel = "test"
    send_anomaly_report(
        client_mock, test_channel, plot_file, metric_name, anomaly_df, "date"
    )
    expected_message = "Hello everyone! Good news: there were no outliers found for the last 2 days for the metric 'test'"
    client_mock.files_upload.assert_called_once_with(
        file=plot_file,
        channels=test_channel,
        initial_comment=expected_message,
        thread_ts=None,
    )
