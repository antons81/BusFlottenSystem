# Базовый образ Python (лёгкий и стабильный)
FROM python:3.12-slim

RUN groupadd -r pyuser && useradd -r -g pyuser -m -d /home/pyuser -s /sbin/nologin pyuser

# Устанавливаем системные зависимости (нужны для psycopg2 и компиляции)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаём рабочую директорию
WORKDIR /app

# Сначала копируем только requirements.txt (чтобы кэшировать слои)
COPY requirements.txt .

# Устанавливаем все Python-библиотеки
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

COPY --chown=pyuser:pyuser . .

USER pyuser

# Открываем порт FastAPI
EXPOSE 8000
EXPOSE 8501

# Команда запуска по умолчанию (FastAPI в режиме разработки)
CMD ["./start_app.sh"]
