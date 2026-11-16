
import pandas as pd
import numpy as np
from pathlib import Path

INPUT_FILE = Path("data/messy/payments.csv")
OUTPUT_FILE = Path("data/processed/payments.csv")

MEMBERS_FILE = Path("data/processed/members.csv")
MEMBERSHIPS_FILE = Path("data/processed/memberships.csv")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

print("Loading payment dataset...")

df = pd.read_csv(INPUT_FILE, dtype={"payment_id": "string",
                                    "member_id": "string",
                                    "membership_id": "string"})

original_rows = len(df)

print(f"Rows Loaded: {len(df):,}")
print(f"Columns Loaded: {len(df.columns)}")

required_columns = [
    "payment_id", "member_id", "membership_id",
    "payment_date", "amount", "payment_method",
    "payment_status", "refund_amount", "created_at"
]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

# Load valid member and membership IDs
members_df = pd.read_csv(
    MEMBERS_FILE,
    dtype={"member_id": "string"}
)

memberships_df = pd.read_csv(
    MEMBERSHIPS_FILE,
    dtype={
        "membership_id": "string",
        "member_id": "string"
    }
)

valid_member_ids = set(members_df["member_id"].dropna())
valid_membership_ids = set(
    memberships_df["membership_id"].dropna()
)

# Standardize text columns
text_columns = [
    "payment_id", "member_id", "membership_id",
    "payment_method", "payment_status"
]

for col in text_columns:
    df[col] = df[col].astype("string").str.strip()

# Standardize payment methods
df["payment_method"] = (
    df["payment_method"]
    .str.upper()
    .str.strip()
)

method_mapping = {
    "CASH": "CASH",
    "UPI": "UPI",
    "CARD": "CARD",
    "CREDIT CARD": "CARD",
    "DEBIT CARD": "CARD",
    "BANK TRANSFER": "BANK_TRANSFER",
    "BANK_TRANSFER": "BANK_TRANSFER"
}

df["payment_method"] = df["payment_method"].replace(
    method_mapping
)

# Standardize payment statuses
df["payment_status"] = (
    df["payment_status"]
    .str.upper()
    .str.strip()
)

status_mapping = {
    "SUCCESS": "SUCCESS",
    "SUCCESSFUL": "SUCCESS",
    "COMPLETED": "SUCCESS",
    "FAILED": "FAILED",
    "PENDING": "PENDING",
    "REFUNDED": "REFUNDED"
}

df["payment_status"] = df["payment_status"].replace(
    status_mapping
)

valid_methods = {
    "CASH", "UPI", "CARD", "BANK_TRANSFER"
}

valid_statuses = {
    "SUCCESS", "FAILED", "PENDING", "REFUNDED"
}

# Convert dates
df["payment_date"] = pd.to_datetime(
    df["payment_date"],
    errors="coerce",
    format="mixed"
).dt.normalize()

df["created_at"] = pd.to_datetime(
    df["created_at"],
    errors="coerce",
    format="mixed"
)

# Convert numeric columns
df["amount"] = pd.to_numeric(
    df["amount"],
    errors="coerce"
)

df["refund_amount"] = pd.to_numeric(
    df["refund_amount"],
    errors="coerce"
)

# Count invalid values before removing rows
invalid_payment_dates = int(
    df["payment_date"].isna().sum()
)

invalid_created_dates = int(
    df["created_at"].isna().sum()
)

invalid_amounts = int(
    df["amount"].isna().sum()
)

invalid_refunds = int(
    df["refund_amount"].isna().sum()
)

invalid_methods = int(
    (~df["payment_method"].isin(valid_methods)).sum()
)

invalid_statuses = int(
    (~df["payment_status"].isin(valid_statuses)).sum()
)

# Replace missing refund amounts with zero
df["refund_amount"] = df["refund_amount"].fillna(0)

# Identify missing essential values
missing_ids = int(
    df[["payment_id", "member_id", "membership_id"]]
    .isna()
    .any(axis=1)
    .sum()
)

# Identify duplicate payment IDs
duplicate_payment_ids = int(
    df["payment_id"].duplicated(keep="first").sum()
)

# Validate foreign keys
invalid_member_fk = int(
    (~df["member_id"].isin(valid_member_ids)).sum()
)

invalid_membership_fk = int(
    (~df["membership_id"].isin(valid_membership_ids)).sum()
)

# Validate numeric values
negative_amounts = int(
    (df["amount"] < 0).sum()
)

negative_refunds = int(
    (df["refund_amount"] < 0).sum()
)

refund_exceeds_payment = int(
    (df["refund_amount"] > df["amount"]).sum()
)

# Remove invalid and duplicate records
df = df.dropna(
    subset=[
        "payment_id",
        "member_id",
        "membership_id",
        "payment_date",
        "amount",
        "payment_method",
        "payment_status",
        "created_at"
    ]
)

df = df.drop_duplicates(
    subset=["payment_id"],
    keep="first"
)

# Remove invalid categorical values
df = df[
    df["payment_method"].isin(valid_methods)
    & df["payment_status"].isin(valid_statuses)
]

# Remove invalid numeric values
df = df[
    (df["amount"] > 0)
    & (df["refund_amount"] >= 0)
    & (df["refund_amount"] <= df["amount"])
]

# Remove invalid foreign keys
df = df[
    df["member_id"].isin(valid_member_ids)
    & df["membership_id"].isin(valid_membership_ids)
]

# Ensure payment member matches membership owner
membership_owner = memberships_df.set_index(
    "membership_id"
)["member_id"]

expected_member_id = df["membership_id"].map(
    membership_owner
)

df = df[
    df["member_id"] == expected_member_id
]

# Save cleaned dataset
df.to_csv(
    OUTPUT_FILE,
    index=False
)

final_rows = len(df)
rows_removed = original_rows - final_rows

print("\nPayment Cleaning Completed!")

print(f"Original Rows: {original_rows:,}")
print(f"Final Rows: {final_rows:,}")
print(f"Rows Removed: {rows_removed:,}")

print(f"\nInvalid Payment Dates: {invalid_payment_dates}")
print(f"Invalid Created Dates: {invalid_created_dates}")
print(f"Invalid Amounts: {invalid_amounts}")
print(f"Invalid Refund Amounts: {invalid_refunds}")
print(f"Invalid Payment Methods: {invalid_methods}")
print(f"Invalid Payment Statuses: {invalid_statuses}")

print(f"\nMissing IDs: {missing_ids}")
print(f"Duplicate Payment IDs: {duplicate_payment_ids}")
print(f"Invalid Member Foreign Keys: {invalid_member_fk}")
print(f"Invalid Membership Foreign Keys: {invalid_membership_fk}")

print(f"\nNegative Amounts: {negative_amounts}")
print(f"Negative Refunds: {negative_refunds}")
print(f"Refunds Exceeding Payment: {refund_exceeds_payment}")

print("\nMissing Values After Cleaning:")
print(df.isna().sum())

print(f"\nSaved to: {OUTPUT_FILE}")