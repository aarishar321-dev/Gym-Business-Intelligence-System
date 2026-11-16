import pandas as pd
import pathlib as Path

#Configurations
INPUT_FILE = Path.Path("data/messy/members.csv")
OUTPUT_DIR = Path.Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "members.csv"

VALID_GENDERS = ["Male", "Female", "Other"]
VALID_AQUISITION_SOURCES = ["WhatsApp","Instagram","Google","Referral","Walk-in","Website"]

#load dataset
print("Loading members dataset...")
df = pd.read_csv(INPUT_FILE)
print(f"Rows Loaded: {len(df):,}")
print(f"Columns Loaded: {len(df.columns)}")

#Standardize column names
df.columns = (df.columns.str.strip().str.lower())

#Clean text columns
text_columns = ["name","gender","acquisition_source"]

for column in text_columns:
    df[column] = (df[column].astype(str).str.strip())

#Standardize name capitalization
df["name"] = (df["name"].str.title())

#Standardize gender
df["gender"] = (df["gender"].str.title())
df.loc[~df["gender"].isin(VALID_GENDERS), "gender"] = pd.NA

#Standardize acquisition source
df["acquisition_source"] = (df["acquisition_source"].str.lower().str.strip())
source_mapping = {
    "whatsapp": "WhatsApp",
    "instagram": "Instagram",
    "google": "Google",
    "referral": "Referral",
    "walk-in": "Walk-in",
    "walk in": "Walk-in",
    "website": "Website"
}
df["acquisition_source"] = df["acquisition_source"].map(source_mapping)

#Clean phone numbers

df["phone"] = (
    df["phone"]
    .astype("string")
    .str.replace(r"\D", "", regex=True)
)

#Extract the final 10 digits
df["phone"] = df["phone"].apply(
    lambda phone: phone[-10:]
    if pd.notna(phone) and len(phone) >= 10
    else pd.NA
)

#Add India's country code
df["phone"] = df["phone"].apply(
    lambda phone: "+91" + phone
    if pd.notna(phone)
    else pd.NA
)

#Convert date columns
date_columns = ["date_of_birth","join_date","created_at"]
for column in date_columns:
    df[column] = pd.to_datetime(df[column], errors="coerce")

#Remove duplicate members IDs
before = len(df)
df = df.drop_duplicates(subset=["member_id"],keep="first")
duplicates_removed = before - len(df)

#Validate phone numbers
valid_phone = (df["phone"].str.match(r"^\+91[6-9]\d{9}$",na=False))
invalid_phone_count = (~valid_phone).sum()

#Validate join dates
today = pd.Timestamp.today().normalize()
invalid_join_dates = ((df["join_date"] > today) | (df["join_date"].isna())).sum()

#Validate date of birth
invalid_dob = ((df["date_of_birth"] > today)).sum()

#Remove impossible records
df = df[df["member_id"].notna()]
df = df[df["phone"].notna()]
df = df[df["join_date"].notna()]
df = df[df["acquisition_source"].notna()]

#Sort data 
df = df.sort_values(by="member_id")

#Save cleaned dataset
df.to_csv(OUTPUT_FILE,index=False)

#Cleaning Summary
print("\nMembers Cleaning Completed!")
print(f"Original Rows : {before:,}")
print(f"Final Rows : {len(df):,}")
print(
    f"Invalid phone numbers detected: "
    f"{invalid_phone_count:,}"
)
print(
    f"Invalid date of birth values detected: "
    f"{invalid_dob:,}"
)

print(
    f"Invalid join dates detected: "
    f"{invalid_join_dates:,}"
)

print("\nMissing values after cleaning:")

print(
    df.isna()
    .sum()
)

print("\nSaved to:")
print(OUTPUT_FILE)