
import pandas as pd
from pathlib import Path

# File paths
INPUT_FILE = Path("data/messy/memberships.csv")
MEMBERS_FILE = Path("data/processed/members.csv")
OUTPUT_FILE = Path("data/processed/memberships.csv")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

print("Loading membership dataset...")

# Load data
df = pd.read_csv(INPUT_FILE, dtype={"membership_id": "string", "member_id": "string"})

members_df = pd.read_csv(
    MEMBERS_FILE,
    dtype={"member_id": "string"}
)

original_rows = len(df)

print(f"Rows Loaded: {original_rows:,}")
print(f"Columns Loaded: {len(df.columns)}")


# Standardize column names
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)


# Clean text columns
text_columns = [
    "membership_id",
    "member_id",
    "plan",
    "status"
]

for column in text_columns:
    if column in df.columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
        )


# Standardize membership plans
plan_mapping = {
    "monthly": "Monthly",
    "month": "Monthly",
    "monthly plan": "Monthly",
    "quarterly": "Quarterly",
    "quarter": "Quarterly",
    "quarterly plan": "Quarterly",
    "half-yearly": "Half-Yearly",
    "half yearly": "Half-Yearly",
    "half_yearly": "Half-Yearly",
    "half-yearly plan": "Half-Yearly",
    "yearly": "Yearly",
    "annual": "Yearly",
    "annually": "Yearly",
    "yearly plan": "Yearly"
}

df["plan"] = (
    df["plan"]
    .str.lower()
    .map(plan_mapping)
)


# Standardize membership statuses
status_mapping = {
    "active": "ACTIVE",
    "expired": "EXPIRED",
    "cancelled": "CANCELLED",
    "canceled": "CANCELLED"
}

df["status"] = (
    df["status"]
    .str.lower()
    .map(status_mapping)
)


# Convert dates
date_columns = [
    "start_date",
    "end_date",
    "created_at"
]

for column in date_columns:
    df[column] = pd.to_datetime(
        df[column],
        errors="coerce",
        dayfirst=False
    )


# Clean price
df["price"] = (
    df["price"]
    .astype("string")
    .str.replace("₹", "", regex=False)
    .str.replace(",", "", regex=False)
    .str.strip()
)

df["price"] = pd.to_numeric(
    df["price"],
    errors="coerce"
)


# Check invalid values
invalid_start_dates = df["start_date"].isna().sum()
invalid_end_dates = df["end_date"].isna().sum()

invalid_prices = (
    df["price"].isna() |
    (df["price"] < 0)
).sum()

invalid_plans = df["plan"].isna().sum()
invalid_statuses = df["status"].isna().sum()


# Check missing IDs
missing_ids = (
    df["membership_id"].isna() |
    df["member_id"].isna()
)

# Remove records without essential IDs
df = df.loc[~missing_ids].copy()


# Remove duplicate membership IDs
duplicate_ids = df["membership_id"].duplicated(keep="first")

duplicate_id_count = duplicate_ids.sum()

df = df.loc[~duplicate_ids].copy()


# Validate membership date logic
invalid_date_order = (
    df["start_date"].notna() &
    df["end_date"].notna() &
    (df["end_date"] < df["start_date"])
)

invalid_date_order_count = invalid_date_order.sum()

df = df.loc[~invalid_date_order].copy()


# Validate member foreign keys
valid_member_ids = set(
    members_df["member_id"].dropna().astype(str)
)

invalid_member_fk = ~df["member_id"].isin(valid_member_ids)

invalid_member_fk_count = invalid_member_fk.sum()

df = df.loc[~invalid_member_fk].copy()


# Remove rows with invalid essential business values
invalid_essential_values = (
    df["plan"].isna() |
    df["status"].isna() |
    df["price"].isna() |
    (df["price"] < 0) |
    df["start_date"].isna() |
    df["end_date"].isna()
)

invalid_essential_count = invalid_essential_values.sum()

df = df.loc[~invalid_essential_values].copy()


# Save cleaned dataset
df.to_csv(
    OUTPUT_FILE,
    index=False
)


# Cleaning summary
print("\nMembership Cleaning Completed!")

print(f"Original Rows: {original_rows:,}")
print(f"Final Rows: {len(df):,}")
print(f"Rows Removed: {original_rows - len(df):,}")

print(f"\nInvalid Start Dates: {invalid_start_dates}")
print(f"Invalid End Dates: {invalid_end_dates}")
print(f"Invalid Prices: {invalid_prices}")
print(f"Invalid Plans: {invalid_plans}")
print(f"Invalid Statuses: {invalid_statuses}")

print(f"\nMissing Membership/Member IDs: {missing_ids.sum()}")
print(f"Duplicate Membership IDs: {duplicate_id_count}")
print(f"Invalid Date Order: {invalid_date_order_count}")
print(f"Invalid Member Foreign Keys: {invalid_member_fk_count}")
print(f"Invalid Essential Values: {invalid_essential_count}")

print("\nMissing Values After Cleaning:")
print(df.isna().sum())

print(f"\nSaved to: {OUTPUT_FILE}")