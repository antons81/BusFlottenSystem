import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import os
from generate_pdf_report import generate_pdf_report
from auto_reports import create_weekly_report

scheduler = BackgroundScheduler()

def weekly_report_job():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Автоматический еженедельный отчёт запущен")
    try:
        pdf_path = generate_pdf_report("weekly")
        print(f"✅ PDF создан: {pdf_path}")
        
        # Отправляем на почту
        send_report_email(pdf_path, "weekly")
        
    except Exception as e:
        print(f"❌ Ошибка при создании еженедельного отчёта: {e}")

def monthly_report_job():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Автоматический ежемесячный отчёт запущен")
    try:
        pdf_path = generate_pdf_report("monthly")
        print(f"✅ PDF создан: {pdf_path}")
        
        send_report_email(pdf_path, "monthly")
        
    except Exception as e:
        print(f"❌ Ошибка при создании ежемесячного отчёта: {e}")

def start_scheduler():
    print("🕒 Запуск планировщика отчётов...")

    # Каждый понедельник в 8:00 утра — weekly report
    scheduler.add_job(
        weekly_report_job,
        trigger=CronTrigger(day_of_week='mon', hour=8, minute=0),
        id='weekly_report',
        replace_existing=True
    )

    # 1-го числа каждого месяца в 8:00 — monthly report
    scheduler.add_job(
        monthly_report_job,
        trigger=CronTrigger(day=1, hour=8, minute=0),
        id='monthly_report',
        replace_existing=True
    )

    scheduler.start()
    print("✅ Планировщик запущен (еженедельный по понедельникам, ежемесячный 1-го числа)")

# Для теста
if __name__ == "__main__":
    start_scheduler()
    print("Scheduler работает. Нажмите Ctrl+C для остановки.")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()