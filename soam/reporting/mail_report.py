# mail_report.py
"""
Mail Report
-----------
Mail creator and sender. Its a postprocess that sends a report with
the model forecasts.
"""
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from os.path import basename
from pathlib import Path
import smtplib
from typing import List, Tuple, Union

from soam.cfg import MAIL_TEMPLATE, get_smtp_cred
from soam.constants import PROJECT_NAME
from soam.core.step import Step

DEFAULT_SUBJECT = "[{end_date}]Forecast report for {metric_name}"
DEFAULT_SIGNATURE = PROJECT_NAME

logger = logging.getLogger(__name__)


class MailReport:
    """
    MailReport
    ----------
    Builds and sends reports via mail.
    """

    def __init__(self, mail_recipients_list: List[str], metric_name: str):
        """
        Create MailReport object.

        Parameters
        ----------
        mail_recipients_list : list of str
            The mails of the recipients for the report.
        metric_name : str
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
        current_date : str
            Date when the report will be sent.
        plot_filename : str or pathlib.Path
             Path of the forecast plot to send.
        subject : str
            Subject of the email.
        signature : str
            Signature for the email.
        """
        logger.info(f"Sending email report to: {self.mail_recipients_list}")

        mime_img, mime_img_name = self._get_mime_images(Path(plot_filename))
        subject, msg_body = self._build_subject_n_msg_body(
            subject, signature, self.metric_name, current_date, mime_img_name
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
        smtp_credentials: dict,
        mail_recipients: List[str],
        subject: str,
        mail_body: str,
        mime_image_list: List[MIMEImage],
        attachments: List[str],
    ):
        """
        Send a report email.
        TODO: review method, may be static

        Parameters
        ----------
        smtp_credentials : dict
            Credentials for the SMTP service.
        mail_recipients : list of str
            The mails of the recipients for the report.
            TODO: this data is on self.
        subject : str
            Subject of the email.
        mail_body : str
            The message to be sent
        mime_image_list : list of email.mime.image.MIMEImage
            List of images to sent
        attachments : list of str
            List of files to attach in the email.
        """
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
        self, subject: str, signature: str, metric_name: str, end_date, mime_img: str
    ) -> Tuple[str, str]:
        """
        Creates the subject and message body
        TODO: review method, may be static

        Parameters
        ----------
        subject : str
            The subject to format
        signature : str
            The message signature
        metric_name : str
            The name for the metric
        end_date : ?
            ?
        mime_img : str
            The path to the mime image.

        Returns
        -------
        str
            The subject of the email.
        str
            The message body of the email.
        """
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

    def _get_mime_images(self, plot_filename: Path) -> Tuple[MIMEImage, str]:
        """
        Extract images from local dir paths.
        TODO: review method, may be static

        Parameters
        ----------
        plot_filename : pathlib.Path
            The path to the plot image.

        Returns
        -------
        MIMEImage
            The image MIME document.
        str
            The plot filename.
        """
        with plot_filename.open("rb") as img_file:
            msg_image = MIMEImage(img_file.read())
            img_name = str(plot_filename)
            msg_image.add_header("Content-Id", f"<{img_name}>")

        return msg_image, img_name

    def _format_link(self, factor: str) -> str:
        """
        TODO: review unused method

        Parameters
        ----------
        factor

        Returns
        -------

        """
        return f"<a href=#{factor}>{factor}</a>"


class MailReportTask(Step, MailReport):
    """
    MailReportTask
    --------------
    Builds the task that sends reports via mail."""

    def __init__(self, mail_recipients_list: List[str], metric_name: str, **kwargs):
        """
        Initialization of the Mail Report Task.

        Parameters
        ----------
        mail_recipients_list: List[str]
            List of the recipients of the email to be sent.
        metric_name: str
            Name of the performance metric being measured.
        """
        Step.__init__(self, **kwargs)  # type: ignore
        MailReport.__init__(self, mail_recipients_list, metric_name)

    def run(  # type: ignore
        self,
        current_date: str,
        plot_filename: Union[Path, str],
        subject: str = DEFAULT_SUBJECT,
        signature: str = DEFAULT_SIGNATURE,
    ):
        """
        Run the Mail Report Task.

        Parameters
        ----------
        current_date: str,
            Current datetime as string.
        plot_filename: Union[Path, str],
            The path and filename of the plot.
        subject: str = DEFAULT_SUBJECT,
            The subject for the email.
        signature: str = DEFAULT_SIGNATURE,
            Signature for the email.
        Returns
        -------
        Mail Report Task
            Sends the report via email.
        """
        return self.send(current_date, plot_filename, subject, signature)
