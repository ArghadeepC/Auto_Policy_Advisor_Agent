# pyrefly: ignore [missing-import]
from .email_utils import send_email_via_gmail


def send_email_tool(args: dict):

    if "recipient_email" in args and "to_email" not in args:
        args["to_email"] = args["recipient_email"]

    if "body" in args and "body_text" not in args:
        args["body_text"] = args["body"]

    required = [
        "to_email",
        "subject",
        "body_text",
        "from_email",
    ]

    missing = [k for k in required if k not in args]

    if missing:
        print(
            f"Missing args: {missing} | Passed args: {args}"
        )

        return {
            "status": "error",
            "message": (
                f"Missing arguments: {', '.join(missing)}"
            ),
        }

    # Optional PDF/file attachments
    attachments = args.get("attachments", [])

    if isinstance(attachments, str):
        attachments = [attachments]

    return send_email_via_gmail(
        to_email=args["to_email"],
        subject=args["subject"],
        body_text=args["body_text"],
        from_email=args["from_email"],
        attachments=attachments,
    )