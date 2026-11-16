from pathlib import Path
import os

import pandas as pd
import psycopg
from psycopg import sql
from dotenv import load_dotenv


# Find the project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load database credentials
load_dotenv(PROJECT_ROOT / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


# Define the CSV-to-database mappings
TABLE_CONFIG = {
    "members": {
        "columns": [
            "member_id",
            "name",
            "phone",
            "join_date",
            "acquisition_source",
            "gender",
            "date_of_birth",
            "created_at",
        ],
        "mapping": {
            "member_id": "member_id",
            "name": "name",
            "phone": "phone",
            "join_date": "join_date",
            "acquisition_source": "acquisition_source",
            "gender": "gender",
            "date_of_birth": "date_of_birth",
            "created_at": "created_at",
        },
    },

    "leads": {
        "columns": [
            "lead_id",
            "name",
            "phone",
            "source",
            "enquiry_date",
            "status",
            "interested_plan",
            "created_at",
            "converted_member_id",
        ],
        "mapping": {
            "lead_id": "lead_id",
            "name": "name",
            "phone": "phone",
            "source": "source",
            "enquiry_date": "enquiry_date",
            "status": "status",
            "interested_plan": "interested_plan",
            "created_at": "created_at",
            "converted_member_id": "converted_member_id",
        },
    },

    "memberships": {
        "columns": [
            "membership_id",
            "member_id",
            "plan",
            "status",
            "start_date",
            "end_date",
            "price",
            "created_at",
        ],
        "mapping": {
            "membership_id": "membership_id",
            "member_id": "member_id",
            "plan": "plan",
            "status": "status",
            "start_date": "start_date",
            "end_date": "end_date",
            "price": "price",
            "created_at": "created_at",
        },
    },

    "attendance": {
        "columns": [
            "attendance_id",
            "member_id",
            "check_in_date",
            "check_in_time",
            "duration",
            "session_type",
            "created_at",
        ],
        "mapping": {
            "attendance_id": "attendance_id",
            "member_id": "member_id",
            "check_in_date": "check_in_date",
            "check_in_time": "check_in_time",
            "session_duration": "duration",
            "session_type": "session_type",
            "created_at": "created_at",
        },
    },

    "payments": {
        "columns": [
            "payment_id",
            "member_id",
            "membership_id",
            "payment_date",
            "amount",
            "payment_method",
            "payment_status",
            "refund_amount",
            "created_at",
        ],
        "mapping": {
            "payment_id": "payment_id",
            "member_id": "member_id",
            "membership_id": "membership_id",
            "payment_date": "payment_date",
            "amount": "amount",
            "payment_method": "payment_method",
            "payment_status": "payment_status",
            "refund_amount": "refund_amount",
            "created_at": "created_at",
        },
    },

    "followups": {
        "columns": [
            "followup_id",
            "lead_id",
            "followup_date",
            "followup_type",
            "status",
            "outcome",
        ],
        "mapping": {
            "followup_id": "followup_id",
            "lead_id": "lead_id",
            "followup_date": "followup_date",
            "followup_type": "followup_type",
            "status": "status",
            "outcome": "outcome",
        },
    },
}


# Load one CSV and prepare its database records
def prepare_records(table_name):

    csv_path = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / f"{table_name}.csv"
    )

    df = pd.read_csv(csv_path)

    # Derive enquiry_date from the lead creation timestamp
    if table_name == "leads":
        df["enquiry_date"] = (
            pd.to_datetime(df["created_at"], errors="coerce")
            .dt.date
        )

    config = TABLE_CONFIG[table_name]

    # Rename CSV columns to match PostgreSQL columns
    df = df.rename(columns=config["mapping"])

    # Keep only the columns required by the database
    df = df[config["columns"]]

    # Convert missing values to Python None
    df = df.astype(object).where(pd.notna(df), None)

    # Convert DataFrame rows into dictionaries
    records = df.to_dict(orient="records")

    return records


# Insert records into one PostgreSQL table
def load_table(conn, table_name):

    config = TABLE_CONFIG[table_name]
    columns = config["columns"]

    records = prepare_records(table_name)

    # Build a parameterized INSERT statement
    insert_query = sql.SQL(
        "INSERT INTO {} ({}) VALUES ({}) "
        "ON CONFLICT DO NOTHING"
    ).format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(
            sql.Identifier(column)
            for column in columns
        ),
        sql.SQL(", ").join(
            sql.Placeholder(column)
            for column in columns
        ),
    )

    with conn.cursor() as cur:
        cur.executemany(insert_query, records)

        affected_rows = cur.rowcount

    print(
        f"{table_name}: "
        f"{len(records)} CSV rows processed, "
        f"{affected_rows} rows inserted."
    )


# Run the complete database loading process
def main():

    # Respect foreign-key dependencies
    load_order = [
        "members",
        "leads",
        "memberships",
        "attendance",
        "payments",
        "followups",
    ]

    print("Starting FitCore Gym database loading...")

    try:
        with psycopg.connect(**DB_CONFIG) as conn:

            # All table loads share one transaction
            for table_name in load_order:
                load_table(conn, table_name)

        print("Database loading completed successfully.")

    except Exception as error:
        print("Database loading failed.")
        print("The transaction was rolled back.")
        print(error)


if __name__ == "__main__":
    main()