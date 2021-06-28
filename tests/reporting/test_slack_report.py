"""Slack report test."""

from soam.reporting.slack_report import SlackMessage

SLACK_MSG_TEMPLATE = """
Hello {{ user }}, welcome to SOAM {{ version }}"""


def test_slack_message_object(tmp_path):
    """Test slack message object."""
    temp_file = tmp_path / "mytemp.txt"
    temp_file_content = "test text"
    temp_file.write_text(temp_file_content)
    template_params = dict(user="test", version="0.1.0")
    slack_msg = SlackMessage(
        SLACK_MSG_TEMPLATE, arguments=template_params, attachment=temp_file
    )
    assert slack_msg.message == SLACK_MSG_TEMPLATE.format(**template_params)
    assert slack_msg.attachment == temp_file.resolve()
    assert slack_msg.attachment.read_text() == temp_file_content
