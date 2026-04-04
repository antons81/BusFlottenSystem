from generate_pdf_report import generate_pdf_report
from ai_analysis import generate_ai_summary
from datetime import datetime
import smtplib
import os
import pytz
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# ====================== E-MAIL VERSAND ======================

berlin = pytz.timezone('Europe/Berlin')

def send_report_email(pdf_path: str, report_type: str = "weekly"):
    """Sendet den PDF-Bericht per E-Mail"""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    email_to  = os.getenv("REPORT_EMAIL_TO", "")

    if not smtp_user or not smtp_pass or not email_to:
        print("⚠️ E-Mail nicht konfiguriert — SMTP_USER, SMTP_PASSWORD, REPORT_EMAIL_TO fehlen")
        return False

    period = "Wöchentlicher" if report_type == "weekly" else "Monatlicher"
    subject = f"go:on – {period} Flottenbericht {datetime.now(tz=berlin).strftime('%d.%m.%Y')}"

    msg = MIMEMultipart()
    msg['From']    = smtp_user
    msg['To']      = email_to
    msg['Subject'] = subject

    body = f"""Guten Tag,

anbei erhalten Sie den automatisch erstellten {period.lower()}en Flottenbericht 
der go:on Gesellschaft für Bus- und Schienenverkehr mbH.

Berichtsdatum: {datetime.now(tz=berlin).strftime('%d.%m.%Y %H:%M')} Uhr

Mit freundlichen Grüßen
go:on Flottenmanagement-System
"""
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # PDF anhängen
    with open(pdf_path, "rb") as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{os.path.basename(pdf_path)}"'
        )
        msg.attach(part)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, email_to, msg.as_string())
        print(f"✅ Bericht per E-Mail versendet an: {email_to}")
        return True
    except Exception as e:
        print(f"❌ E-Mail Fehler: {e}")
        return False


# ====================== BERICHTSFUNKTIONEN ======================


def create_weekly_report(send_email=False):
    """Создаёт еженедельный отчёт (и optionally отправляет на email)"""
    print(f"[{datetime.now(tz=berlin).strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Создание еженедельного отчёта...")
    
    try:
        pdf_path = generate_pdf_report("weekly")
        print(f"✅ PDF создан: {pdf_path}")
        
        if send_email:
            success = send_report_email(pdf_path, "weekly")
            if success:
                print("✅ Отчёт отправлен на email")
            else:
                print("⚠️ PDF создан, но email отправить не удалось")
        
        return pdf_path
    except Exception as e:
        print(f"❌ Ошибка при создании отчёта: {e}")
        return None


def create_monthly_report(send_email=False):
    """Создаёт ежемесячный отчёт"""
    print(f"[{datetime.now(tz=berlin).strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Создание ежемесячного отчёта...")
    
    try:
        pdf_path = generate_pdf_report("monthly")
        print(f"✅ PDF создан: {pdf_path}")
        
        if send_email:
            send_report_email(pdf_path, "monthly")
        
        return pdf_path
    except Exception as e:
        print(f"❌ Ошибка при создании отчёта: {e}")
        return None


# ====================== SCHEDULER ======================
def start_scheduler():
    """Startet den automatischen Berichts-Scheduler"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BackgroundScheduler(timezone="Europe/Berlin")

        # Wöchentlich: jeden Montag um 07:00 Uhr
        scheduler.add_job(
            lambda: create_weekly_report(send_email=True),
            CronTrigger(day_of_week='mon', hour=7, minute=0),
            id='weekly_report',
            name='Wöchentlicher Flottenbericht',
            replace_existing=True
        )

        # Monatlich: 1. des Monats um 07:00 Uhr
        scheduler.add_job(
            lambda: create_monthly_report(send_email=True),
            CronTrigger(day=1, hour=7, minute=0),
            id='monthly_report',
            name='Monatlicher Flottenbericht',
            replace_existing=True
        )

        scheduler.start()
        print("✅ Scheduler gestartet:")
        print("   • Wochenbericht: jeden Montag um 07:00 Uhr")
        print("   • Monatsbericht: 1. des Monats um 07:00 Uhr")
        return scheduler

    except ImportError:
        print("⚠️ APScheduler nicht installiert — pip install apscheduler")
        return None


if __name__ == "__main__":
    create_weekly_report(send_email=False)