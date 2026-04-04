#!/bin/bash
echo "🚀 Запуск Go:On Busflotten System..."

# Запускаем scheduler в фоне
echo "→ Запуск планировщика отчётов..."
python scheduler.py &

# Даём немного времени на запуск scheduler
sleep 3

# Запускаем основной дашборд
echo "→ Запуск Streamlit дашборда на http://0.0.0.0:8501"
exec streamlit run streamlit_dashboard.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true