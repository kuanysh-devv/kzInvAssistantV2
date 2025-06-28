#!/bin/bash
set -e

# 1. Connect to default postgres database to create user & database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'superuser') THEN
      CREATE USER superuser WITH PASSWORD 'postgres';
    END IF;

    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'kzinvbot') THEN
      CREATE DATABASE kzinvbot;
    END IF;

    GRANT ALL PRIVILEGES ON DATABASE kzinvbot TO superuser;
  END
  \$\$;
EOSQL

# 2. Connect to the created database and grant schema permissions
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname kzinvbot <<-EOSQL
  GRANT ALL ON SCHEMA public TO superuser;
  ALTER SCHEMA public OWNER TO superuser;
EOSQL