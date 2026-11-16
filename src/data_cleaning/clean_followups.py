
import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/messy/followups.csv")
OUTPUT_FILE = Path("data/processed/followups.csv")
LEADS_FILE = Path("data/processed/leads.csv")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

print("Loading followups dataset...")

df = pd.read_csv(
    INPUT_FILE,
    dtype={
        "followup_id": "string",
        "lead_id": "string"
    }
)

original_rows = len(df)

print(f"Rows Loaded: {len(df):,}")
print(f"Columns Loaded: {len(df.columns)}")

required_columns = [
    "followup_id",
    "lead_id",
    "followup_date",
    "followup_type",
    "status",
    "outcome"
]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

# Load valid lead IDs
leads_df = pd.read_csv(
    LEADS_FILE,
    dtype={"lead_id": "string"}
)

valid_lead_ids = set(
    leads_df["lead_id"].dropna()
)

# Clean text columns
text_columns = [
    "followup_id",
    "lead_id",
    "followup_type",
    "status",
    "outcome"
]

for col in text_columns:
    df[col] = df[col].astype("string").str.strip()

# Convert blank strings to missing values
for col in text_columns:
    df[col] = df[col].replace("", pd.NA)

# Standardize follow-up types
df["followup_type"] = (
    df["followup_type"].str.upper().str.strip()
)

followup_type_mapping = {
    "CALL": "CALL",
    "PHONE CALL": "CALL",
    "WHATSAPP": "WHATSAPP",
    "MESSAGE": "WHATSAPP",
    "SMS": "SMS",
    "EMAIL": "EMAIL",
    "IN_PERSON": "IN_PERSON",
    "IN-PERSON": "IN_PERSON",
    "IN PERSON": "IN_PERSON"
}

df["followup_type"] = (
    df["followup_type"].replace(followup_type_mapping)
)

valid_followup_types = {
    "CALL",
    "WHATSAPP",
    "SMS",
    "EMAIL",
    "IN_PERSON"
}

# Standardize follow-up statuses
df["status"] = df["status"].str.upper().str.strip()

status_mapping = {
    "COMPLETED": "COMPLETED",
    "DONE": "COMPLETED",
    "PENDING": "PENDING",
    "SCHEDULED": "SCHEDULED",
    "CANCELLED": "CANCELLED",
    "CANCELED": "CANCELLED",
    "FAILED": "FAILED"
}

df["status"] = df["status"].replace(status_mapping)

valid_statuses = {
    "COMPLETED",
    "PENDING",
    "SCHEDULED",
    "CANCELLED",
    "FAILED"
}

# Standardize outcomes
df["outcome"] = (
    df["outcome"].str.upper().str.strip()
)

outcome_mapping = {
    "INTERESTED": "INTERESTED",
    "NO RESPONSE": "NO_RESPONSE",
    "NO_RESPONSE": "NO_RESPONSE",
    "NOT INTERESTED": "NOT_INTERESTED",
    "NOT_INTERESTED": "NOT_INTERESTED",
    "CONVERTED": "CONVERTED",
    "CALL BACK": "CALL_BACK",
    "CALL_BACK": "CALL_BACK",
    "FOLLOW UP": "FOLLOW_UP",
    "FOLLOW_UP": "FOLLOW_UP",
    "UNREACHABLE": "UNREACHABLE"
}

df["outcome"] = df["outcome"].replace(outcome_mapping)

valid_outcomes = {
    "INTERESTED",
    "NO_RESPONSE",
    "NOT_INTERESTED",
    "CONVERTED",
    "CALL_BACK",
    "FOLLOW_UP",
    "UNREACHABLE"
}

# Convert follow-up dates
df["followup_date"] = pd.to_datetime(
    df["followup_date"],
    errors="coerce",
    format="mixed"
)

# Count invalid values before cleaning
invalid_dates = int(
    df["followup_date"].isna().sum()
)

invalid_types = int(
    (~df["followup_type"].isin(valid_followup_types)).sum()
)

invalid_statuses = int(
    (~df["status"].isin(valid_statuses)).sum()
)

invalid_outcomes = int(
    (
        df["outcome"].notna()
        & ~df["outcome"].isin(valid_outcomes)
    ).sum()
)

missing_ids = int(
    df[["followup_id", "lead_id"]]
    .isna()
    .any(axis=1)
    .sum()
)

duplicate_followup_ids = int(
    df["followup_id"].duplicated(keep="first").sum()
)

invalid_lead_foreign_keys = int(
    (~df["lead_id"].isin(valid_lead_ids)).sum()
)

# Remove rows missing essential fields
df = df.dropna(
    subset=[
        "followup_id",
        "lead_id",
        "followup_date",
        "followup_type",
        "status"
    ]
)

# Remove duplicate follow-up IDs
df = df.drop_duplicates(
    subset=["followup_id"],
    keep="first"
)

# Remove invalid categories
df = df[
    df["followup_type"].isin(valid_followup_types)
    & df["status"].isin(valid_statuses)
]

# Keep missing outcomes as missing
df = df[
    df["outcome"].isna()
    | df["outcome"].isin(valid_outcomes)
]

# Remove follow-ups referring to invalid leads
df = df[
    df["lead_id"].isin(valid_lead_ids)
]

# Save cleaned dataset
df.to_csv(
    OUTPUT_FILE,
    index=False
)

final_rows = len(df)
rows_removed = original_rows - final_rows

print("\nFollow-up Cleaning Completed!")

print(f"Original Rows: {original_rows:,}")
print(f"Final Rows: {final_rows:,}")
print(f"Rows Removed: {rows_removed:,}")

print(f"\nInvalid Follow-up Dates: {invalid_dates}")
print(f"Invalid Follow-up Types: {invalid_types}")
print(f"Invalid Statuses: {invalid_statuses}")
print(f"Invalid Outcomes: {invalid_outcomes}")

print(f"\nMissing IDs: {missing_ids}")
print(f"Duplicate Follow-up IDs: {duplicate_followup_ids}")
print(f"Invalid Lead Foreign Keys: {invalid_lead_foreign_keys}")

print("\nMissing Values After Cleaning:")
print(df.isna().sum())

print(f"\nSaved to: {OUTPUT_FILE}")