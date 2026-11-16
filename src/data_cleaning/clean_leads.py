
import pandas as pd
import numpy as np
import re
from pathlib import Path

INPUT_FILE = Path("data/messy/leads.csv")
OUTPUT_FILE = Path("data/processed/leads.csv")
MEMBERS_FILE = Path("data/processed/members.csv")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

print("Loading leads dataset...")

df = pd.read_csv(
    INPUT_FILE,
    dtype={
        "lead_id": "string",
        "phone": "string",
        "converted_member_id": "string"
    }
)

original_rows = len(df)

print(f"Rows Loaded: {len(df):,}")
print(f"Columns Loaded: {len(df.columns)}")

required_columns = [
    "lead_id",
    "name",
    "phone",
    "created_at",
    "source",
    "interested_plan",
    "status",
    "converted_member_id"
]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

# Load valid member IDs
members_df = pd.read_csv(
    MEMBERS_FILE,
    dtype={"member_id": "string"}
)

valid_member_ids = set(
    members_df["member_id"].dropna()
)

# Clean text fields
text_columns = [
    "lead_id",
    "name",
    "phone",
    "source",
    "interested_plan",
    "status",
    "converted_member_id"
]

for col in text_columns:
    df[col] = df[col].astype("string").str.strip()

# Standardize names
df["name"] = (
    df["name"]
    .str.replace(r"\s+", " ", regex=True)
    .str.title()
)

# Convert blank strings to missing values
for col in text_columns:
    df[col] = df[col].replace("", pd.NA)

# Standardize lead sources
df["source"] = df["source"].str.upper()

source_mapping = {
    "WHATSAPP": "WHATSAPP",
    "INSTAGRAM": "INSTAGRAM",
    "GOOGLE": "GOOGLE",
    "REFERRAL": "REFERRAL",
    "WALK-IN": "WALK_IN",
    "WALK IN": "WALK_IN",
    "WALK_IN": "WALK_IN",
    "WEBSITE": "WEBSITE"
}

df["source"] = df["source"].replace(source_mapping)

valid_sources = {
    "WHATSAPP",
    "INSTAGRAM",
    "GOOGLE",
    "REFERRAL",
    "WALK_IN",
    "WEBSITE"
}

# Standardize interested plans
df["interested_plan"] = (
    df["interested_plan"]
    .str.upper()
    .str.strip()
)

plan_mapping = {
    "MONTHLY": "MONTHLY",
    "QUARTERLY": "QUARTERLY",
    "HALF-YEARLY": "HALF_YEARLY",
    "HALF YEARLY": "HALF_YEARLY",
    "HALF_YEARLY": "HALF_YEARLY",
    "YEARLY": "YEARLY"
}

df["interested_plan"] = (
    df["interested_plan"].replace(plan_mapping)
)

valid_plans = {
    "MONTHLY",
    "QUARTERLY",
    "HALF_YEARLY",
    "YEARLY"
}

# Standardize lead statuses
df["status"] = df["status"].str.upper().str.strip()

status_mapping = {
    "NEW": "NEW",
    "QUALIFIED": "QUALIFIED",
    "FOLLOW_UP": "FOLLOW_UP",
    "FOLLOW-UP": "FOLLOW_UP",
    "FOLLOW UP": "FOLLOW_UP",
    "CONVERTED": "CONVERTED",
    "LOST": "LOST",
    "NOT_INTERESTED": "NOT_INTERESTED",
    "NOT INTERESTED": "NOT_INTERESTED"
}

df["status"] = df["status"].replace(status_mapping)

valid_statuses = {
    "NEW",
    "QUALIFIED",
    "FOLLOW_UP",
    "CONVERTED",
    "LOST",
    "NOT_INTERESTED"
}

# Clean phone numbers
def clean_phone(value):
    if pd.isna(value):
        return pd.NA

    digits = re.sub(r"\D", "", str(value))

    # Remove Indian country code when present
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]

    # Accept only valid 10-digit Indian mobile numbers
    if re.fullmatch(r"[6-9]\d{9}", digits):
        return "+91" + digits

    return pd.NA

df["phone"] = df["phone"].apply(clean_phone)

# Convert lead creation dates
df["created_at"] = pd.to_datetime(
    df["created_at"],
    errors="coerce",
    format="mixed"
)

# Count invalid values before removing rows
invalid_dates = int(df["created_at"].isna().sum())

invalid_phones = int(df["phone"].isna().sum())

invalid_sources = int(
    (~df["source"].isin(valid_sources)).sum()
)

invalid_plans = int(
    (
        df["interested_plan"].notna()
        & ~df["interested_plan"].isin(valid_plans)
    ).sum()
)

invalid_statuses = int(
    (~df["status"].isin(valid_statuses)).sum()
)

missing_lead_ids = int(df["lead_id"].isna().sum())

duplicate_lead_ids = int(
    df["lead_id"].duplicated(keep="first").sum()
)

invalid_converted_member_ids = int(
    (
        df["converted_member_id"].notna()
        & ~df["converted_member_id"].isin(valid_member_ids)
    ).sum()
)

# Identify converted leads without a valid member ID
converted_without_member = int(
    (
        (df["status"] == "CONVERTED")
        & (
            df["converted_member_id"].isna()
            | ~df["converted_member_id"].isin(valid_member_ids)
        )
    ).sum()
)

# Remove records with missing essential fields
df = df.dropna(
    subset=[
        "lead_id",
        "name",
        "phone",
        "created_at",
        "source",
        "status"
    ]
)

# Remove duplicate lead IDs
df = df.drop_duplicates(
    subset=["lead_id"],
    keep="first"
)

# Remove invalid categorical values
df = df[
    df["source"].isin(valid_sources)
    & df["status"].isin(valid_statuses)
]

# Remove invalid interested plans only when a value exists
df = df[
    df["interested_plan"].isna()
    | df["interested_plan"].isin(valid_plans)
]

# Remove invalid converted member references
df = df[
    df["converted_member_id"].isna()
    | df["converted_member_id"].isin(valid_member_ids)
]

# Converted leads must reference a valid member
df = df[
    (df["status"] != "CONVERTED")
    | df["converted_member_id"].notna()
]

# Save cleaned leads
df.to_csv(
    OUTPUT_FILE,
    index=False
)

final_rows = len(df)
rows_removed = original_rows - final_rows

print("\nLead Cleaning Completed!")

print(f"Original Rows: {original_rows:,}")
print(f"Final Rows: {final_rows:,}")
print(f"Rows Removed: {rows_removed:,}")

print(f"\nInvalid Dates: {invalid_dates}")
print(f"Invalid Phone Numbers: {invalid_phones}")
print(f"Invalid Sources: {invalid_sources}")
print(f"Invalid Interested Plans: {invalid_plans}")
print(f"Invalid Statuses: {invalid_statuses}")

print(f"\nMissing Lead IDs: {missing_lead_ids}")
print(f"Duplicate Lead IDs: {duplicate_lead_ids}")
print(f"Invalid Converted Member IDs: {invalid_converted_member_ids}")
print(f"Converted Leads Without Valid Member: {converted_without_member}")

print("\nMissing Values After Cleaning:")
print(df.isna().sum())

print(f"\nSaved to: {OUTPUT_FILE}")