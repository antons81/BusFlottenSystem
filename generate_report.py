import pandas as pd
from app.secure_db import execute_safe_query
from datetime import datetime
import os
import pytz

def generate_report(report_type="weekly"):
    """Генерирует красивый HTML-отчёт на немецком языке"""
    berlin = pytz.timezone('Europe/Berlin')
    timestamp = datetime.now(tz=berlin).strftime("%Y-%m-%d_%H-%M")
    filename = f"reports/GoOn_{report_type}_report_{timestamp}.html"
    
    # Получаем данные
    buses = execute_safe_query("SELECT COUNT(*) as c FROM busse")[0]['c']
    active = execute_safe_query("SELECT COUNT(*) as c FROM busse WHERE status = 'aktiv'")[0]['c']
    overdue = execute_safe_query("""
        SELECT COUNT(*) as c FROM wartung 
        WHERE status = 'überfällig' OR naechste_faellig < CURRENT_DATE
    """)[0]['c']
    
    df_fahrten = pd.DataFrame(execute_safe_query("""
        SELECT 
            f.datum, 
            COALESCE(b.kennzeichen, 'Unbekannt') as kennzeichen, 
            f.km_gesamt, 
            f.auslastung_prozent 
        FROM fahrten f
        LEFT JOIN busse b ON f.bus_id = b.bus_id
        ORDER BY f.datum DESC
        LIMIT 15
    """))
    
    html_content = f"""
    <html>
    <head>
        <title>Go:On - {report_type.capitalize()} Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f9f9f9; }}
            h1 {{ color: #1f77b4; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #1f77b4; color: white; }}
            .kpi {{ font-size: 18px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h1>🚌 Go:On - {report_type.capitalize()} Report</h1>
        <p><strong>Datum der Erstellung:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        
        <h2>Wichtige Kennzahlen</h2>
        <p class="kpi">Gesamte Busse: <strong>{buses}</strong></p>
        <p class="kpi">Aktive Busse: <strong>{active}</strong></p>
        <p class="kpi">Überfällige Wartungen: <strong>{overdue}</strong></p>
        
        <h2>Letzte Fahrten</h2>
    """
    
    if not df_fahrten.empty:
        html_content += df_fahrten.to_html(index=False, escape=False)
    else:
        html_content += "<p>Keine Fahrtendaten vorhanden.</p>"
    
    html_content += """
        <hr>
        <p><small>Automatisierter Prototyp-Bericht | Go:On</small></p>
    </body>
    </html>
    """
    
    os.makedirs("reports", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ Отчёт успешно создан: {filename}")
    return filename

# Для ручного запуска
if __name__ == "__main__":
    print("=== Генерация отчёта ===")
    print("1. Еженедельный отчёт")
    print("2. Ежемесячный отчёт")
    print("3. Ручной отчёт")
    choice = input("Выберите тип (1/2/3): ")
    
    if choice == "1":
        generate_report("weekly")
    elif choice == "2":
        generate_report("monthly")
    else:
        generate_report("manual")