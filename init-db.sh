#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create schemas for different services
    CREATE SCHEMA IF NOT EXISTS leads;
    CREATE SCHEMA IF NOT EXISTS evolution_api;
    CREATE SCHEMA IF NOT EXISTS litellm;
EOSQL
