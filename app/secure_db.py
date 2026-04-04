from sqlalchemy import create_engine, text
import hvac
import os
from functools import lru_cache
from typing import Dict

# ====================== VAULT CLIENT ======================
@lru_cache()
def get_vault_client():
    """Создаём клиент для Vault"""
    client = hvac.Client(
        url=os.getenv("VAULT_ADDR", "http://vault:8200"),
        token=os.getenv("VAULT_TOKEN", "myroot")
    )
    return client

# ====================== GET CREDENTIALS FROM VAULT ======================
def get_db_credentials() -> Dict:
    """Получаем логин и пароль из Vault"""
    try:
        client = get_vault_client()
        secret = client.secrets.kv.v2.read_secret_version(path="database/postgres")
        data = secret['data']['data']
        print("✅ Успешно получили секреты из Vault")
        return data
    except Exception as e:
        print(f"⚠️ Ошибка при получении из Vault: {type(e).__name__}: {e}")
        raise RuntimeError(f"Не удалось получить секреты из Vault: {e}")
# ====================== DATABASE ENGINE ======================
@lru_cache()
def get_db_engine():
    """Создаём подключение к PostgreSQL"""
    creds = get_db_credentials()
    database_url = f"postgresql://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['dbname']}"
    engine = create_engine(database_url, pool_pre_ping=True, echo=False)
    return engine

# ====================== SAFE QUERY EXECUTOR ======================
def execute_safe_query(sql: str):
    """Безопасная функция для выполнения SQL запросов (для LangChain агента)"""
    engine = get_db_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        return [dict(row) for row in result.mappings()]
