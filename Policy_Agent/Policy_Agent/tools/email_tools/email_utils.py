import os
import mimetypes
import smtplib

from email.message import EmailMessage


SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL")
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_email_via_gmail(
    to_email: str,
    subject: str,
    body_text: str,
    from_email: str = None,
    attachments: list = None,
):

    from_email = from_email or SENDER_EMAIL

    if not APP_PASSWORD or not from_email:
        return {
            "status": "error",
            "message": (
                "Email credentials are not configured. "
                "Set GMAIL_SENDER_EMAIL and GMAIL_APP_PASSWORD in .env."
            ),
        }

    if attachments is None:
        attachments = []

    if isinstance(attachments, str):
        attachments = [attachments]

    # --------------------------------------------------
    # Create email
    # --------------------------------------------------

    msg = EmailMessage()

    msg["To"] = to_email
    msg["From"] = from_email
    msg["Subject"] = subject

    msg.set_content(body_text)

    # --------------------------------------------------
    # Add local file attachments
    # --------------------------------------------------

    attachment_errors = []

    for file_path in attachments:

        if not file_path:
            continue

        try:
            if not os.path.isfile(file_path):
                attachment_errors.append(
                    f"Attachment not found: {file_path}"
                )
                continue

            with open(file_path, "rb") as file:
                file_data = file.read()

            mime_type, _ = mimetypes.guess_type(file_path)

            if mime_type:
                maintype, subtype = mime_type.split("/", 1)
            else:
                maintype = "application"
                subtype = "octet-stream"

            msg.add_attachment(
                file_data,
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(file_path),
            )

        except Exception as e:
            attachment_errors.append(
                f"Unable to attach {file_path}: {str(e)}"
            )

    # --------------------------------------------------
    # Send email
    # --------------------------------------------------

    try:

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

            smtp.login(
                from_email,
                APP_PASSWORD,
            )

            smtp.send_message(msg)

        result = {
            "status": "success",
            "message": "Email sent successfully.",
        }

        if attachment_errors:
            result["attachment_errors"] = attachment_errors

        result["attachments"] = [
            os.path.basename(path)
            for path in attachments
            if path and os.path.isfile(path)
        ]

        return result

    except smtplib.SMTPAuthenticationError:

        return {
            "status": "error",
            "message": (
                "Authentication failed — "
                "check the Gmail app password."
            ),
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e),
        }