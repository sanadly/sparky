import smtplib
import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import asyncio
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

    async def send_offer_email(self, to_email: str, offer_id: str, product_name: str, consumption: str, price: str):
        """
        Sends an email with the offer details to the user.
        """
        subject = f"Dein Angebot von Intense Energy: {offer_id}"
        
        # Plain Text Fallback
        text_body = f"""
        Hallo!

        Vielen Dank für dein Interesse an Intense Energy.
        
        Hier sind die Details zu deinem Angebot:
        
        Angebotsnummer: {offer_id}
        Tarif: {product_name}
        Jahresverbrauch: {consumption} kWh
        Geschätzter Preis: {price}
        
        Um das Angebot anzunehmen, klicke bitte hier:
        https://intense-energy.de/accept-offer?id={offer_id}
        (Dies wandelt das Angebot in einen Vertrag um)
        
        Oder antworte einfach auf diese E-Mail.
        
        Viele Grüße,
        Dein Intense Energy Team
        """

        # HTML Body
        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; color: #333; line-height: 1.6; }}
              .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9; }}
              .header {{ text-align: center; padding-bottom: 20px; border-bottom: 2px solid #007bff; margin-bottom: 20px; }}
              .header h1 {{ color: #007bff; margin: 0; }}
              .offer-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
              .offer-item {{ margin-bottom: 10px; }}
              .offer-label {{ font-weight: bold; color: #555; }}
              .offer-value {{ font-size: 1.1em; color: #000; }}
              .footer {{ text-align: center; font-size: 0.8em; color: #777; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; }}
              .cta {{ display: block; width: fit-content; margin: 20px auto; padding: 10px 20px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }}
            </style>
          </head>
          <body>
            <div class="container">
              <div class="header">
                <h1>⚡ Intense Energy</h1>
                <p>Dein persönliches Angebot</p>
              </div>
              
              <p>Hallo!</p>
              <p>Vielen Dank für dein Interesse. Hier ist das Angebot, das wir für dich berechnet haben:</p>
              
              <div class="offer-card">
                <div class="offer-item">
                  <div class="offer-label">Angebotsnummer</div>
                  <div class="offer-value">{offer_id}</div>
                </div>
                <div class="offer-item">
                  <div class="offer-label">Tarif</div>
                  <div class="offer-value">{product_name}</div>
                </div>
                <div class="offer-item">
                  <div class="offer-label">Jahresverbrauch</div>
                  <div class="offer-value">{consumption} kWh</div>
                </div>
                <div class="offer-item">
                  <div class="offer-label">Geschätzter Preis</div>
                  <div class="offer-value" style="color: #28a745; font-weight: bold;">{price}</div>
                </div>
              </div>
              
              <p style="text-align: center; margin-top: 20px;">
                Um das Angebot anzunehmen, klicke bitte auf den folgenden Button:
              </p>
              
              <a href="https://intense-energy.de/accept-offer?id={offer_id}" class="cta">JETZT ANGEBOT ANNEHMEN</a>
              
              <p style="text-align: center; font-size: 0.9em; color: #555;">
                (Hinweis: Dies ist ein simulierter Link. In einem echten System würde dieser Klick das Angebot ID {offer_id} an einen SAP-Endpunkt senden, um es in einen verbindlichen Vertrag umzuwandeln.)
              </p>
              
              <div class="footer">
                <p>Intense Energy GmbH | Musterstraße 123 | 12345 Musterstadt</p>
                <p>Tel: 0123 456789 | E-Mail: tarifrechner@srv-x.de</p>
              </div>
            </div>
          </body>
        </html>
        """

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
                logger.info("📧 Polling for new emails...")
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
