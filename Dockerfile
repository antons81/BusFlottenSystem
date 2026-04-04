# Базовый образ Python (лёгкий и стабильный)
FROM python:3.12-slim

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
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта
COPY . .

# Открываем порт FastAPI
EXPOSE 8000

# Команда запуска по умолчанию (FastAPI в режиме разработки)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--reload"]
