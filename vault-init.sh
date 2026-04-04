#!/bin/sh
echo '⏳ Ждём запуска Vault...'
until vault status; do
  echo 'Vault не готов, ждём...'
  sleep 2
done
echo '✅ Vault готов, записываем секреты...'
vault kv put secret/database/postgres \
  username="$POSTGRES_USER" \
  password="$POSTGRES_PASSWORD" \
  host=postgres \
  port=5432 \
  dbname="$POSTGRES_DB"
echo '✅ Секреты записаны!'