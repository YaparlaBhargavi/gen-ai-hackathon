# app/agents/email_agent.py
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import EmailLog
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class EmailAgent:
    def __init__(self, user_id: int, db_session: Session):
        self.user_id = user_id
        self.db = db_session
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.sender_email = os.getenv("SENDER_EMAIL", "")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")

    async def process_email_query(self, query: str) -> Dict[str, Any]:
        """Process email-related queries"""
        query_lower = query.lower()

        if "send" in query_lower:
            return await self.send_email(query)
        elif "schedule" in query_lower:
            return await self.schedule_email(query)
        else:
            return await self.get_email_help()

    async def send_email(self, query: str) -> Dict[str, Any]:
        """Send email from natural language"""
        # Extract recipient
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", query)
        if not email_match:
            return {
                "status": "error",
                "message": "Please provide an email address (e.g., 'Send email to john@example.com')",
            }

        recipient = email_match.group(0)

        # Extract subject
        subject_match = re.search(
            r"about\s+(.+?)(?:$|with|and|for)", query, re.IGNORECASE
        )
        subject = (
            subject_match.group(1).strip()
            if subject_match
            else "Task Reminder from AI Assistant"
        )

        # Build email body
        body_lines = [
            "From: AI Productivity Assistant",
            "",
            f"Regarding: {query}",
            "",
            "This is an automated reminder from your AI Productivity Assistant.",
            "Best regards,",
            "AI Assistant",
        ]
        body = "\n".join(body_lines)

        # Try to send email if credentials are configured
        email_sent = False
        error_message = None

        if self.sender_email and self.sender_password:
            try:
                msg = MIMEMultipart()
                msg["From"] = self.sender_email
                msg["To"] = recipient
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))

                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                server.quit()
                email_sent = True
            except Exception as e:
                error_message = str(e)
                email_sent = False

        # Log email
        email_log = EmailLog(
            user_id=self.user_id,
            recipient=recipient,
            subject=subject,
            body=body,
            status="sent" if email_sent else "failed",
            sent_at=datetime.now() if email_sent else None,
            error_message=error_message,
        )
        self.db.add(email_log)
        self.db.commit()

        if email_sent:
            return {
                "status": "success",
                "response": f"📧 Email sent to {recipient}!\nSubject: {subject}",
            }
        else:
            response_lines = [
                "⚠️ Email was logged but not sent. SMTP not configured.",
                "",
                "To enable email sending, configure SMTP settings in .env file.",
                "",
                f"Email would have been sent to: {recipient}",
                f"Subject: {subject}",
            ]
            return {"status": "warning", "response": "\n".join(response_lines)}

    async def schedule_email(self, query: str) -> Dict[str, Any]:
        """Schedule an email for later"""
        # Extract recipient
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", query)
        if not email_match:
            return {"status": "error", "message": "Please provide an email address"}

        recipient = email_match.group(0)

        # Extract time
        time_match = re.search(
            r"at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)", query, re.IGNORECASE
        )
        if not time_match:
            return {
                "status": "error",
                "message": "Please specify when to send (e.g., 'Schedule email to john@example.com for tomorrow at 9am')",
            }

        # For now, just log that scheduling is coming soon
        return {
            "status": "info",
            "response": f"📧 Email scheduling is coming soon! I'll remind you to send this email to {recipient}.\n\nFeature under development: Scheduled emails",
        }

    async def get_email_help(self) -> Dict[str, Any]:
        """Get email help"""
        response_lines = [
            "📧 Email Commands:",
            "",
            "• Send email to john@example.com about project deadline",
            "• Schedule email to team@company.com for tomorrow at 9am",
            "",
            f"SMTP Configured: {'✅ Yes' if self.sender_email else '❌ No'}",
            "To enable email sending, add SMTP credentials to .env file",
        ]

        return {"status": "success", "response": "\n".join(response_lines)}
