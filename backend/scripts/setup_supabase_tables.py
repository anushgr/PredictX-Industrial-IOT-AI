#!/usr/bin/env python3
"""
Create the Supabase tables used by PredictX Industrial AI.

This script connects to the Supabase Postgres instance and executes the SQL files:
- supabase/sensor_raw_records.sql
- supabase/sensor_aggregates.sql

Usage examples:
  python scripts/setup_supabase_tables.py
  python scripts/setup_supabase_tables.py --database-url "postgresql://postgres:YOUR_PASSWORD@host:5432/postgres"

Environment variables:
  DATABASE_URL
  SUPABASE_DB_HOST, SUPABASE_DB_PORT, SUPABASE_DB_NAME,
  SUPABASE_DB_USER, SUPABASE_DB_PASSWORD
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
SQL_FILES = [
    ROOT / "supabase" / "sensor_raw_records.sql",
    ROOT / "supabase" / "sensor_aggregates.sql",
    ROOT / "supabase" / "machine_predictions.sql",
]


def parse_database_url(database_url: str) -> dict[str, str | int]:
    if not database_url:
        raise ValueError("DATABASE_URL is empty")

    # Accept both a strict URI and the common project note format where the password may contain '@'.
    if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
        try:
            result = urlsplit(database_url)
            username = unquote(result.username or "postgres")
            password = unquote(result.password or "")
            host = result.hostname or "db.jfhnigjrmzcamxgdaohq.supabase.co"
            port = result.port or 5432
            dbname = result.path.lstrip("/") or "postgres"
            if password:
                return {
                    "host": host,
                    "port": port,
                    "dbname": dbname,
                    "user": username,
                    "password": password,
                }
        except Exception:
            pass

        # Fallback parser for strings like:
        # postgresql://postgres:Anushgr@123@host:5432/postgres
        body = database_url.split("//", 1)[1]
        creds, host_part = body.rsplit("@", 1)
        username, password = creds.split(":", 1)
        host_port, dbname = host_part.split("/", 1)
        host, port_str = host_port.rsplit(":", 1)
        # Decode URL-encoded characters (e.g., %40 → @)
        password = unquote(password)
        username = unquote(username)
        return {
            "host": host,
            "port": int(port_str),
            "dbname": dbname,
            "user": username,
            "password": password,
        }

    raise ValueError("DATABASE_URL must start with postgresql:// or postgres://")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create Supabase tables for PredictX")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", ""))
    parser.add_argument("--host", default=os.getenv("SUPABASE_DB_HOST", "db.jfhnigjrmzcamxgdaohq.supabase.co"))
    parser.add_argument("--port", type=int, default=int(os.getenv("SUPABASE_DB_PORT", "5432")))
    parser.add_argument("--dbname", default=os.getenv("SUPABASE_DB_NAME", "postgres"))
    parser.add_argument("--user", default=os.getenv("SUPABASE_DB_USER", "postgres"))
    parser.add_argument("--password", default=os.getenv("SUPABASE_DB_PASSWORD", ""))
    return parser.parse_args()


def load_sql(file_path: Path) -> str:
    if not file_path.exists():
        raise FileNotFoundError(f"Missing SQL file: {file_path}")
    return file_path.read_text(encoding="utf-8")


def main() -> int:
    args = parse_args()

    if args.database_url:
        conn_kwargs = parse_database_url(args.database_url)
    else:
        if not args.password:
            print("ERROR: database password required via --password, SUPABASE_DB_PASSWORD, or DATABASE_URL")
            return 1
        conn_kwargs = {
            "host": args.host,
            "port": args.port,
            "dbname": args.dbname,
            "user": args.user,
            "password": args.password,
        }

    connection = psycopg2.connect(**conn_kwargs, sslmode="require")
    connection.autocommit = True

    try:
        with connection.cursor() as cursor:
            for sql_file in SQL_FILES:
                sql = load_sql(sql_file)
                print(f"Applying {sql_file.name} ...")
                cursor.execute(sql)
                print(f"Applied {sql_file.name}")

        print("Supabase table setup completed successfully.")
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    sys.exit(main())
