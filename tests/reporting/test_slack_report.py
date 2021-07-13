"""Slack report test."""

from pathlib import Path
from unittest.mock import MagicMock

from jinja2 import Template
import pytest

from soam.reporting.slack_report import SlackMessage, send_slack_message

SLACK_MSG_TEMPLATE = """
Hello {{ user }}, welcome to SOAM {{ version }}"""


def test_slack_message_object_with_path(tmp_path):
    """Test slack message object."""
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


def test_slack_message_object_with_file(tmp_path):
    """Test slack message object."""
    temp_file = tmp_path / "mytemp.txt"
    temp_file_content = "test text"
    temp_file.write_text(temp_file_content)
    template_params = dict(user="test", version="0.1.0")
    slack_msg = SlackMessage(
        SLACK_MSG_TEMPLATE, arguments=template_params, attachment=temp_file.open()
    )
    assert slack_msg.message == Template(SLACK_MSG_TEMPLATE).render(**template_params)
    assert slack_msg.attachment == str(temp_file.resolve())
    assert Path(slack_msg.attachment).read_text() == temp_file_content


def test_send_slack_message_no_attachment():
    client_mock = MagicMock()
    template_params = dict(user="test", version="0.1.0")
    slack_msg = SlackMessage(SLACK_MSG_TEMPLATE, arguments=template_params)
    test_channel = "test"
    send_slack_message(client_mock, channel=test_channel, msg=slack_msg)
    client_mock.chat_postMessage.assert_called_once_with(
        channel=test_channel, text=slack_msg.message, thread_ts=None
    )


def test_send_slack_message_with_attachment(tmp_path):
    client_mock = MagicMock()
    temp_file = tmp_path / "mytemp.txt"
    temp_file_content = "test text"
    temp_file.write_text(temp_file_content)
    template_params = dict(user="test", version="0.1.0")
    slack_msg = SlackMessage(
        SLACK_MSG_TEMPLATE, arguments=template_params, attachment=temp_file
    )
    test_channel = "test"
    send_slack_message(client_mock, channel=test_channel, msg=slack_msg)
    client_mock.files_upload.assert_called_once_with(
        file=slack_msg.attachment,
        channels=test_channel,
        initial_comment=slack_msg.message,
        thread_ts=None,
    )


def test_slack_message_with_non_existing_attachment_fails():
    path_mock = MagicMock()
    path_mock.exists.return_value = False
    template_params = dict(user="test", version="0.1.0")
    slack_msg = SlackMessage(
        SLACK_MSG_TEMPLATE, arguments=template_params, attachment=path_mock
    )
    with pytest.raises(ValueError):
        slack_msg.attachment  # pylint: disable=pointless-statement
