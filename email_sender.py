import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os
import pytz

berlin = pytz.timezone('Europe/Berlin')
dt = datetime.now(tz=berlin)

def send_report_email(pdf_path, report_type="weekly"):
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient = os.getenv("REPORT_EMAIL_TO")

    if not all([smtp_user, smtp_password, recipient]):
        print("⚠️ Не все SMTP переменные настроены. Пропускаем отправку.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient
        msg['Subject'] = f"Go:On - {report_type.capitalize()} Bericht {dt.strftime('%d.%m.%Y')}"

        body = f"""
        Guten Tag,

        im Anhang finden Sie den automatischen {report_type} Flottenbericht.

        Mit freundlichen Grüßen
        go:on Flottenmanagement
        """

        msg.attach(MIMEText(body, 'plain'))

        # Прикрепляем PDF
        with open(pdf_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(pdf_path)}")
            msg.attach(part)

        # Отправка
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()

        print(f"✅ Отчёт успешно отправлен на {recipient}")
        return True

    except Exception as e:
        print(f"❌ Ошибка при отправке email: {e}")
        return False