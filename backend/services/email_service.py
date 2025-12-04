import smtplib
import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import asyncio
import os
from jinja2 import Environment, FileSystemLoader
from ..config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.imap_server = settings.IMAP_SERVER
        self.imap_port = settings.IMAP_PORT
        
        # Jinja2 Setup
        template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
        self.env = Environment(loader=FileSystemLoader(template_dir))

    async def send_offer_email(self, to_email: str, offer_id: str, product_name: str, consumption: str, price: str):
        """
        Sends an email with the offer details to the user.
        """
        subject = f"Dein Angebot von Intense Energy: {offer_id}"
        
        # Ensure product_name has a value
        if not product_name or not product_name.strip():
            product_name = "Intense Standard"

        # Plain Text Fallback
        text_body = f"""
        Hallo!

        Vielen Dank für dein Interesse an Intense Energy.
        
        Hier sind die Details zu deinem Angebot:
        
        Angebotsnummer: {offer_id}
        Tarif: {product_name}
        Jahresverbrauch: {consumption} kWh
        Geschätzter Preis: {price}
        
        Antworte einfach auf diese E-Mail, wenn du Fragen hast.
        
        Viele Grüße,
        Dein Intense Energy Team
        """

        # HTML Body
        # HTML Body (Rendered via Jinja2)
        try:
            template = self.env.get_template('offer_email.html')
            html_body = template.render(
                offer_id=offer_id,
                product_name=product_name,
                consumption=consumption,
                price=price
            )
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            # Fallback to simple HTML if template fails
            html_body = f"<html><body><h1>Angebot {offer_id}</h1><p>Preis: {price}</p></body></html>"

        msg = MIMEMultipart("alternative")
        msg['From'] = self.smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        try:
            # Using SMTP_SSL for port 465
            def _send():
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            
            await asyncio.to_thread(_send)
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

    async def send_email(self, to_email: str, subject: str, body: str):
        """
        Sends a generic email.
        """
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            def _send():
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            
            await asyncio.to_thread(_send)
            logger.info(f"✅ Generic email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send generic email: {e}")
            return False

    def check_new_emails(self):
        """
        Connects to IMAP, checks for UNSEEN messages, and returns a list of dicts.
        """
        new_emails = []
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.smtp_user, self.smtp_password)
            mail.select("inbox")

            status, messages = mail.search(None, "UNSEEN")
            if status != "OK":
                return []

            email_ids = messages[0].split()
            for e_id in email_ids:
                status, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Decode Subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        
                        # Decode Sender
                        sender = msg.get("From")
                        
                        # Get Body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                if content_type == "text/plain" and "attachment" not in content_disposition:
                                    body = part.get_payload(decode=True).decode()
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode()

                        new_emails.append({
                            "sender": sender,
                            "subject": subject,
                            "body": body
                        })
                        
            mail.close()
            mail.logout()
            
            if new_emails:
                logger.info(f"📧 Received {len(new_emails)} new emails")
                
            return new_emails

        except Exception as e:
            logger.error(f"❌ Error checking emails: {e}")
            return []

    async def run_email_polling(self, chat_service_instance):
        """
        Runs the email polling loop.
        """
        while True:
            try:
                logger.debug("📧 Polling for new emails...")
                new_emails = await asyncio.to_thread(self.check_new_emails)
                
                for email in new_emails:
                    sender = email["sender"]
                    subject = email["subject"]
                    body = email["body"]
                    
                    logger.info(f"📩 Processing email from {sender}: {subject}")
                    
                    # Clean up body (remove quoted replies)
                    cleaned_body = body
                    lines = body.splitlines()
                    non_quoted_lines = []
                    for line in lines:
                        if line.strip().startswith(">") or line.strip().startswith("On ") and "wrote:" in line:
                             break # Stop at first quote
                        non_quoted_lines.append(line)
                    
                    if non_quoted_lines:
                        cleaned_body = "\n".join(non_quoted_lines).strip()
                    
                    logger.info(f"📝 Cleaned Email Body for LLM: {cleaned_body[:200]}...") # Log first 200 chars

                    # Use ChatService to handle the email content as a message
                    response = await chat_service_instance.handle_message(sender, cleaned_body)
                    reply_text = response.get("reply")
                    
                    if reply_text:
                        # Send Reply
                        await self.send_email(sender, f"Re: {subject}", reply_text)
                    
            except Exception as e:
                error_msg = str(e)
                if "Operation timed out" in error_msg or "60" in error_msg:
                    logger.warning(f"⚠️ Email Polling Timeout: Connection to IMAP server timed out. Retrying...")
                else:
                    logger.error(f"Error in email polling loop: {e}")
                
            await asyncio.sleep(10) # Poll every 10 seconds
