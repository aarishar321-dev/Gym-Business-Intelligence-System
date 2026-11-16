
import pandas as pd
from pathlib import Path

INPUT_FILE = Path("data/messy/attendance.csv")
MEMBERS_FILE = Path("data/processed/members.csv")
OUTPUT_FILE = Path("data/processed/attendance.csv")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

print("Loading attendance dataset...")

df = pd.read_csv(
    INPUT_FILE,
    dtype={
        "attendance_id": "string",
        "member_id": "string"
    }
)

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
    "attendance_id",
    "member_id",
    "session_type"
]

for column in text_columns:
    df[column] = (
        df[column]
        .astype("string")
        .str.strip()
    )


# Standardize session types
session_mapping = {
    "strength training": "Strength Training",
    "strength_training": "Strength Training",
    "cardio": "Cardio",
    "personal training": "Personal Training",
    "personal_training": "Personal Training",
    "pt": "Personal Training",
    "mixed workout": "Mixed Workout",
    "mixed_workout": "Mixed Workout",
    "group class": "Group Class",
    "group_class": "Group Class"
}

df["session_type"] = (
    df["session_type"]
    .str.lower()
    .map(session_mapping)
)


# Convert check-in dates
df["check_in_date"] = pd.to_datetime(
    df["check_in_date"],
    errors="coerce"
).dt.normalize()


# Convert check-in times
df["check_in_time"] = pd.to_datetime(
    df["check_in_time"],
    errors="coerce",
    format="mixed"
).dt.time


# Convert session duration to numeric
df["session_duration"] = pd.to_numeric(
    df["session_duration"],
    errors="coerce"
)


# Check invalid values
invalid_dates = df["check_in_date"].isna().sum()

invalid_times = df["check_in_time"].isna().sum()

invalid_durations = (
    df["session_duration"].isna() |
    (df["session_duration"] <= 0) |
    (df["session_duration"] > 300)
).sum()

invalid_session_types = df["session_type"].isna().sum()


# Check missing IDs
missing_ids = (
    df["attendance_id"].isna() |
    df["member_id"].isna()
)

missing_id_count = missing_ids.sum()

df = df.loc[~missing_ids].copy()


# Remove duplicate attendance IDs
duplicate_ids = df["attendance_id"].duplicated(
    keep="first"
)

duplicate_id_count = duplicate_ids.sum()

df = df.loc[~duplicate_ids].copy()


# Validate member foreign keys
valid_member_ids = set(
    members_df["member_id"].dropna().astype(str)
)

invalid_member_fk = ~df["member_id"].isin(
    valid_member_ids
)

invalid_member_fk_count = invalid_member_fk.sum()

df = df.loc[~invalid_member_fk].copy()


# Remove rows with invalid essential values
invalid_essential_values = (
    df["check_in_date"].isna() |
    df["check_in_time"].isna() |
    df["session_duration"].isna() |
    (df["session_duration"] <= 0) |
    (df["session_duration"] > 300) |
    df["session_type"].isna()
)

invalid_essential_count = invalid_essential_values.sum()

df = df.loc[~invalid_essential_values].copy()


# Convert duration to integer
df["session_duration"] = (
    df["session_duration"].round().astype("int64")
)


# Save cleaned dataset
df.to_csv(
    OUTPUT_FILE,
    index=False
)


# Cleaning summary
print("\nAttendance Cleaning Completed!")

print(f"Original Rows: {original_rows:,}")
print(f"Final Rows: {len(df):,}")
print(f"Rows Removed: {original_rows - len(df):,}")

print(f"\nInvalid Check-in Dates: {invalid_dates}")
print(f"Invalid Check-in Times: {invalid_times}")
print(f"Invalid Session Durations: {invalid_durations}")
print(f"Invalid Session Types: {invalid_session_types}")

print(f"\nMissing IDs: {missing_id_count}")
print(f"Duplicate Attendance IDs: {duplicate_id_count}")
print(f"Invalid Member Foreign Keys: {invalid_member_fk_count}")
print(f"Invalid Essential Values: {invalid_essential_count}")

print("\nMissing Values After Cleaning:")
print(df.isna().sum())

print(f"\nSaved to: {OUTPUT_FILE}")