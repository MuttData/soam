# mail_report.py
"""Mail creator and sender."""
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from os.path import basename
from pathlib import Path
import smtplib
from typing import List, Union

from soam.cfg import MAIL_TEMPLATE, get_smtp_cred
from soam.constants import PARENT_LOGGER, PROJECT_NAME
from soam.step import Step

DEFAULT_SUBJECT = "[{end_date}]Forecast report for {metric_name}"
DEFAULT_SIGNATURE = PROJECT_NAME

logger = logging.getLogger(f"{PARENT_LOGGER}.{__name__}")

"""
MailReport
----------
Class for building and sending a report via mail.
"""


class MailReport:
    """
        Builds and sends an email report.
    """

    def __init__(self, mail_recipients_list: List[str], metric_name: str):
        """
        Create MailReport object.

        Parameters
        ----------
        mail_recipients_list
            Array of the mails to send the report to.
        metric_name
            Name of the metric being forecasted.
        """
        self.mail_recipients_list = mail_recipients_list
        credentials = get_smtp_cred()
        self.credentials = credentials
        self.metric_name = metric_name

    def send(
        self,
        current_date: str,
        plot_filename: Union[Path, str],
        subject: str = DEFAULT_SUBJECT,
        signature: str = DEFAULT_SIGNATURE,
    ):
        """
        Send email report.

        Parameters
        ----------
        current_date
            date the report will be sent.
        plot_filename
            str or pathlib.Path of the forecast plot to send.
        subject
            subject of the mail sent.
        signature
            signature with which to end the mail.
        """
        logger.info(f"Sending email report to: {self.mail_recipients_list}")

        mime_img, mime_img_name = self._get_mime_images(Path(plot_filename))
        subject, msg_body = self._build_subject_n_msg_body(
            subject, signature, self.metric_name, current_date, mime_img_name,
        )

        self._send_mail(
            self.credentials,
            self.mail_recipients_list,
            subject,
            msg_body,
            [mime_img],
            [],
        )

    def _send_mail(
        self,
        smtp_credentials,
        mail_recipients,
        subject,
        mail_body,
        mime_image_list,
        attachments,
    ):
        """Send."""
        user = smtp_credentials.get("user_address")
        password = smtp_credentials.get("password")
        from_address = smtp_credentials["mail_from"]
        host = smtp_credentials["host"]
        port = smtp_credentials["port"]
        logger.info(
            f"""About to send the following email:
                    'From: ' {from_address}
                    'To: ' {mail_recipients}
                    'Subject: ' {subject}
                    'Using host': {host} and port: {port}"""
        )
        logger.error(f"With the following body: \n {mail_body}")

        msg_root = MIMEMultipart("related")
        msg_root["From"] = from_address
        msg_root["Subject"] = subject
        msg_root["To"] = ", ".join(mail_recipients)

        msg_alt = MIMEMultipart("alternative")
        msg_root.attach(msg_alt)

        msg_text = MIMEText(mail_body, "html")
        msg_alt.attach(msg_text)

        for mim_img in mime_image_list:
            msg_root.attach(mim_img)

        for attachment in attachments:
            with open(attachment, "rb") as f:
                part = MIMEApplication(f.read(), Name=basename(attachment))
            part["Content-Disposition"] = 'attachment; filename="%s"' % basename(
                attachment
            )
            msg_root.attach(part)

        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            if user is not None and password is not None:
                server.starttls()
                server.ehlo()
                server.login(user, password)
            server.sendmail(from_address, mail_recipients, msg_root.as_string())
        logger.info("Email sent succesfully")

    def _build_subject_n_msg_body(
        self, subject, signature, metric_name, end_date, mime_img
    ):
        """Build body and subject."""
        if subject == DEFAULT_SUBJECT:
            subject = subject.format(end_date=end_date, metric_name=metric_name)
        logger.debug(f"Mail subject:\n {subject}")

        jparams = {
            "signature": signature,
            "metric_name": metric_name,
            "end_date": end_date,
            "mime_img": mime_img,
        }
        msg_body = getattr(MAIL_TEMPLATE, "mail_body")(**jparams)
        logger.debug(f"html mail body:\n {msg_body}")
        return subject, msg_body

    def _get_mime_images(self, plot_filename: Path):
        """Extract images from local dir paths."""
        with plot_filename.open("rb") as img_file:
            msg_image = MIMEImage(img_file.read())
            img_name = str(plot_filename)
            msg_image.add_header("Content-Id", f"<{img_name}>")

        return msg_image, img_name

    def _format_link(self, factor):
        return f"<a href=#{factor}>{factor}</a>"


class MailReportTask(Step, MailReport):
    def __init__(self, mail_recipients_list: List[str], metric_name: str, **kwargs):
        Step.__init__(self, **kwargs)  # type: ignore
        MailReport.__init__(self, mail_recipients_list, metric_name)

    def run(  # type: ignore
        self,
        current_date: str,
        plot_filename: Union[Path, str],
        subject: str = DEFAULT_SUBJECT,
        signature: str = DEFAULT_SIGNATURE,
    ):
        return self.send(current_date, plot_filename, subject, signature)
