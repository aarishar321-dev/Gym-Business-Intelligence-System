import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

try:
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database();")
            database_name = cur.fetchone()[0]

            print(f"Successfully connected to: {database_name}")

except psycopg.Error as error:
    print("Database connection failed.")
    print(error)