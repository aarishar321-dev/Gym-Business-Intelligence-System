import pandas as pd
import numpy as np
from pathlib import Path


SEED = 42

np.random.seed(SEED)


MEMBERS_FILE = Path("data/raw/members.csv")

OUTPUT_DIR = Path("data/raw")

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


members_df = pd.read_csv(
    MEMBERS_FILE
)


N_LEADS = 650


lead_sources = [
    "WhatsApp",
    "Instagram",
    "Google",
    "Referral",
    "Walk-in",
    "Website"
]

lead_source_probabilities = [
    0.30,
    0.20,
    0.15,
    0.15,
    0.10,
    0.10
]


plans = [
    "Monthly",
    "Quarterly",
    "Half-Yearly",
    "Yearly"
]

plan_probabilities = [
    0.45,
    0.30,
    0.15,
    0.10
]


lead_records = []

used_lead_phones = set()


member_phones = set(
    members_df["phone"].astype(str)
)


today = pd.Timestamp.today().normalize()


conversion_probability = 0.28

converted_count = int(
    N_LEADS * conversion_probability
)


converted_member_rows = (
    members_df
    .sample(
        n=converted_count,
        random_state=SEED
    )
    .reset_index(drop=True)
)


converted_member_ids = set(
    converted_member_rows["member_id"]
)


converted_member_index = 0


lead_names = [
    "Rahul",
    "Arun",
    "Karthik",
    "Vignesh",
    "Sanjay",
    "Praveen",
    "Harish",
    "Naveen",
    "Rohit",
    "Aditya",
    "Arjun",
    "Priya",
    "Divya",
    "Harini",
    "Kavya",
    "Ananya",
    "Shruthi",
    "Keerthana",
    "Pooja",
    "Swathi",
    "Sneha",
    "Aishwarya",
    "Megha",
    "Sahana",
    "Nandhini"
]


for i in range(1, N_LEADS + 1):

    lead_id = f"LEAD{i:04d}"


    is_converted = (
        i <= converted_count
    )


    if is_converted:

        member_row = (
            converted_member_rows
            .iloc[converted_member_index]
        )

        converted_member_index += 1

        name = member_row["name"]

        phone = member_row["phone"]

        converted_member_id = (
            member_row["member_id"]
        )

        status = "CONVERTED"


    else:

        name = np.random.choice(
            lead_names
        )

        converted_member_id = None


        while True:

            first_digit = np.random.choice(
                [
                    "6",
                    "7",
                    "8",
                    "9"
                ]
            )

            remaining_digits = "".join(
                np.random.choice(
                    list("0123456789"),
                    size=9
                )
            )

            phone = (
                "+91"
                + first_digit
                + remaining_digits
            )


            if (
                phone not in used_lead_phones
                and phone not in member_phones
            ):

                used_lead_phones.add(
                    phone
                )

                break


        status = np.random.choice(
            [
                "NEW",
                "QUALIFIED",
                "FOLLOW_UP",
                "LOST",
                "NOT_INTERESTED"
            ],
            p=[
                0.15,
                0.25,
                0.25,
                0.20,
                0.15
            ]
        )


    source = np.random.choice(
        lead_sources,
        p=lead_source_probabilities
    )


    interested_plan = np.random.choice(
        plans,
        p=plan_probabilities
    )


    days_ago = np.random.randint(
        0,
        181
    )


    created_at = (
        today
        - pd.Timedelta(
            days=int(days_ago)
        )
        + pd.Timedelta(
            hours=int(
                np.random.randint(
                    8,
                    22
                )
            ),
            minutes=int(
                np.random.randint(
                    0,
                    60
                )
            ),
            seconds=int(
                np.random.randint(
                    0,
                    60
                )
            )
        )
    )


    if created_at > pd.Timestamp.now():

        created_at = (
            pd.Timestamp.now()
            - pd.Timedelta(
                minutes=int(
                    np.random.randint(
                        1,
                        120
                    )
                )
            )
        )


    lead_records.append({
        "lead_id": lead_id,
        "name": name,
        "phone": phone,
        "created_at": created_at,
        "source": source,
        "interested_plan": interested_plan,
        "status": status,
        "converted_member_id": converted_member_id
    })


leads_df = pd.DataFrame(
    lead_records
)


output_file = (
    OUTPUT_DIR / "leads.csv"
)


leads_df.to_csv(
    output_file,
    index=False
)


print("Lead dataset generated successfully!")

print(f"Rows: {len(leads_df)}")

print(f"Columns: {len(leads_df.columns)}")

print(f"Saved to: {output_file}")


print("\nFirst 10 rows:")

print(
    leads_df.head(10)
)


print("\nMissing values:")

print(
    leads_df.isnull().sum()
)


print("\nDuplicate lead IDs:")

print(
    leads_df["lead_id"]
    .duplicated()
    .sum()
)


print("\nLead status distribution:")

print(
    leads_df["status"]
    .value_counts()
)


print("\nLead source distribution:")

print(
    leads_df["source"]
    .value_counts()
)


print("\nInterested plan distribution:")

print(
    leads_df["interested_plan"]
    .value_counts()
)


print("\nConverted leads:")

print(
    (
        leads_df["status"] == "CONVERTED"
    ).sum()
)


print("\nLeads with converted member IDs:")

print(
    leads_df["converted_member_id"]
    .notna()
    .sum()
)


print("\nInvalid converted member IDs:")

converted_ids = (
    leads_df[
        leads_df["converted_member_id"].notna()
    ]["converted_member_id"]
)

invalid_converted_ids = (
    ~converted_ids.isin(
        members_df["member_id"]
    )
).sum()

print(
    invalid_converted_ids
)


print("\nDuplicate lead phone numbers:")

print(
    leads_df["phone"]
    .duplicated()
    .sum()
)


print("\nLead date range:")

print(
    leads_df["created_at"].min(),
    "to",
    leads_df["created_at"].max()
)


print("\nConverted leads with missing member IDs:")

print(
    leads_df[
        (leads_df["status"] == "CONVERTED")
        & (leads_df["converted_member_id"].isna())
    ].shape[0]
)


print("\nDuplicate converted member IDs:")

converted_member_duplicates = (
    leads_df[
        leads_df["status"] == "CONVERTED"
    ]["converted_member_id"]
    .duplicated()
    .sum()
)

print(
    converted_member_duplicates
)