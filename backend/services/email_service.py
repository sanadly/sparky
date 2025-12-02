import smtplib
import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
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

    def send_offer_email(self, to_email: str, offer_id: str, product_name: str, consumption: str, price: str):
        """
        Sends an email with the offer details to the user.
        """
        subject = f"Dein Angebot von Intense Energy: {offer_id}"
        
        body = f"""
        Hallo!

        Vielen Dank für dein Interesse an Intense Energy.
        
        Hier sind die Details zu deinem Angebot:
        
        Angebotsnummer: {offer_id}
        Tarif: {product_name}
        Jahresverbrauch: {consumption} kWh
        Geschätzter Preis: {price}
        
        Um das Angebot anzunehmen, antworte einfach auf diese E-Mail oder kontaktiere uns telefonisch.
        
        Viele Grüße,
        Dein Intense Energy Team
        """

        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            # Using SMTP_SSL for port 465
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

    def send_email(self, to_email: str, subject: str, body: str):
        """
        Sends a generic email.
        """
        msg = MIMEMultipart()
        msg['From'] = self.smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
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
