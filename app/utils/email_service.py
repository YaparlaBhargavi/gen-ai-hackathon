import os
import smtplib
from email.message import EmailMessage
from email.utils import formatdate
import uuid
import datetime
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_email = os.environ.get("SMTP_EMAIL")
        self.smtp_password = os.environ.get("SMTP_PASSWORD")
        self.smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.environ.get("SMTP_PORT", 465))
        self.is_configured = bool(self.smtp_email and self.smtp_password)

    def _send(self, msg: EmailMessage):
        if not self.is_configured:
            print("[EMAIL SERVICE] Mock send (SMTP not configured in .env).")
            print(f"Subject: {msg['Subject']}\nTo: {msg['To']}\n")
            return False

        try:
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.smtp_email, self.smtp_password)
                server.send_message(msg)
            print(f"[EMAIL SERVICE] Successfully sent email to {msg['To']}")
            return True
        except Exception as e:
            print(f"[EMAIL SERVICE ERROR]: {e}")
            return False

    def send_calendar_invite(self, to_email: str, title: str, description: str, start_time: datetime.datetime, end_time: datetime.datetime = None):
        msg = EmailMessage()
        msg['Subject'] = f"Event Invitation: {title}"
        msg['From'] = self.smtp_email or "aiproductivity@local"
        msg['To'] = to_email
        msg['Date'] = formatdate(localtime=True)
        
        body = f"Hello,\n\nYou have scheduled the following event:\n\nTitle: {title}\nTime: {start_time.strftime('%Y-%m-%d %H:%M')}"
        if description:
            body += f"\nDescription: {description}"
        msg.set_content(body)

        # Generate ICS attachment
        dtstamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        dtstart = start_time.astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        
        if end_time:
            dtend = end_time.astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        else:
            dtend = (start_time + datetime.timedelta(hours=1)).astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        uid = str(uuid.uuid4())
        desc_str = (description or '').replace('\n', '\\n')
        
        ics_content = f"""BEGIN:VCALENDAR\r
VERSION:2.0\r
PRODID:-//AI Productivity Platform//EN\r
METHOD:REQUEST\r
BEGIN:VEVENT\r
UID:{uid}\r
DTSTAMP:{dtstamp}\r
DTSTART:{dtstart}\r
DTEND:{dtend}\r
SUMMARY:{title}\r
DESCRIPTION:{desc_str}\r
END:VEVENT\r
END:VCALENDAR\r
"""

        msg.add_attachment(ics_content.encode('utf-8'), maintype='text', subtype='calendar', filename='invite.ics')

        return self._send(msg)

    def send_reminder(self, to_email: str, title: str, start_time: datetime.datetime):
        msg = EmailMessage()
        msg['Subject'] = f"Reminder: {title} is starting soon!"
        msg['From'] = self.smtp_email or "aiproductivity@local"
        msg['To'] = to_email
        msg['Date'] = formatdate(localtime=True)
        
        msg.set_content(f"Hi there,\n\nThis is a quick reminder that your event '{title}' is starting at {start_time.strftime('%Y-%m-%d %H:%M')}.\n\nDon't be late!")
        return self._send(msg)

email_service = EmailService()
