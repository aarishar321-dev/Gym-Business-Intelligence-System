import pandas as pd
import numpy as np
from pathlib import Path


SEED = 42

np.random.seed(SEED)


LEADS_FILE = Path("data/raw/leads.csv")

OUTPUT_DIR = Path("data/raw")

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


leads_df = pd.read_csv(
    LEADS_FILE,
    parse_dates=["created_at"]
)


followup_types = [
    "WhatsApp",
    "Phone Call",
    "SMS"
]

followup_type_probabilities = [
    0.60,
    0.25,
    0.15
]


followup_records = []

followup_counter = 1

current_time = pd.Timestamp.now()


for _, lead in leads_df.iterrows():

    lead_id = lead["lead_id"]

    lead_created_at = lead["created_at"]

    lead_status = lead["status"]


    if lead_status == "CONVERTED":

        number_of_followups = np.random.choice(
            [1, 2, 3],
            p=[0.55, 0.35, 0.10]
        )

    elif lead_status == "NOT_INTERESTED":

        number_of_followups = np.random.choice(
            [0, 1],
            p=[0.75, 0.25]
        )

    elif lead_status == "LOST":

        number_of_followups = np.random.choice(
            [1, 2, 3],
            p=[0.25, 0.50, 0.25]
        )

    elif lead_status == "NEW":

        number_of_followups = np.random.choice(
            [0, 1],
            p=[0.40, 0.60]
        )

    else:

        number_of_followups = np.random.choice(
            [1, 2, 3, 4],
            p=[0.15, 0.35, 0.35, 0.15]
        )


    for followup_number in range(
        number_of_followups
    ):

        if followup_number == 0:

            days_after_lead = 0

        elif followup_number == 1:

            days_after_lead = 1

        elif followup_number == 2:

            days_after_lead = 3

        else:

            days_after_lead = 7


        scheduled_date = (
            lead_created_at
            + pd.Timedelta(
                days=days_after_lead
            )
        )


        if scheduled_date <= current_time:

            followup_date = scheduled_date

            status = np.random.choice(
                [
                    "COMPLETED",
                    "SKIPPED"
                ],
                p=[
                    0.85,
                    0.15
                ]
            )

        else:

            followup_date = scheduled_date

            status = "PENDING"


        if status == "COMPLETED":

            if lead_status == "CONVERTED":

                outcome = np.random.choice(
                    [
                        "Converted",
                        "Interested",
                        "Follow-up Required"
                    ],
                    p=[
                        0.65,
                        0.25,
                        0.10
                    ]
                )

            elif lead_status == "NOT_INTERESTED":

                outcome = np.random.choice(
                    [
                        "Not Interested",
                        "No Response"
                    ],
                    p=[
                        0.75,
                        0.25
                    ]
                )

            elif lead_status == "LOST":

                outcome = np.random.choice(
                    [
                        "No Response",
                        "Price Concern",
                        "Joined Elsewhere",
                        "Follow-up Required"
                    ],
                    p=[
                        0.45,
                        0.20,
                        0.15,
                        0.20
                    ]
                )

            else:

                outcome = np.random.choice(
                    [
                        "Interested",
                        "Follow-up Required",
                        "No Response"
                    ],
                    p=[
                        0.45,
                        0.35,
                        0.20
                    ]
                )

        elif status == "PENDING":

            outcome = "Pending"

        else:

            outcome = "Skipped"


        followup_type = np.random.choice(
            followup_types,
            p=followup_type_probabilities
        )


        followup_records.append({
            "followup_id": f"FU{followup_counter:05d}",
            "lead_id": lead_id,
            "followup_date": followup_date,
            "followup_type": followup_type,
            "status": status,
            "outcome": outcome
        })


        followup_counter += 1


followups_df = pd.DataFrame(
    followup_records
)


output_file = (
    OUTPUT_DIR / "followups.csv"
)


followups_df.to_csv(
    output_file,
    index=False
)


print("Follow-up dataset generated successfully!")

print(f"Rows: {len(followups_df)}")

print(f"Columns: {len(followups_df.columns)}")

print(f"Saved to: {output_file}")


print("\nFirst 10 rows:")

print(
    followups_df.head(10)
)


print("\nMissing values:")

print(
    followups_df.isnull().sum()
)


print("\nDuplicate follow-up IDs:")

print(
    followups_df["followup_id"]
    .duplicated()
    .sum()
)


print("\nFollow-up status distribution:")

print(
    followups_df["status"]
    .value_counts()
)


print("\nFollow-up type distribution:")

print(
    followups_df["followup_type"]
    .value_counts()
)


print("\nFollow-up outcome distribution:")

print(
    followups_df["outcome"]
    .value_counts()
)


print("\nLead IDs with follow-ups:")

print(
    followups_df["lead_id"].nunique()
)


print("\nLeads without follow-ups:")

print(
    len(leads_df)
    - followups_df["lead_id"].nunique()
)


print("\nInvalid lead IDs:")

invalid_lead_ids = (
    ~followups_df["lead_id"].isin(
        leads_df["lead_id"]
    )
).sum()

print(
    invalid_lead_ids
)


print("\nFollow-up date range:")

print(
    followups_df["followup_date"].min(),
    "to",
    followups_df["followup_date"].max()
)


print("\nFollow-up count per lead:")

followups_per_lead = (
    followups_df
    .groupby("lead_id")
    .size()
)

print(
    followups_per_lead.describe()
)


print("\nConverted leads with follow-ups:")

converted_leads = set(
    leads_df[
        leads_df["status"] == "CONVERTED"
    ]["lead_id"]
)

followup_leads = set(
    followups_df["lead_id"]
)

converted_with_followups = (
    len(
        converted_leads
        & followup_leads
    )
)

print(
    converted_with_followups
)


print("\nFollow-ups scheduled in the future:")

print(
    (
        followups_df["followup_date"]
        > current_time
    ).sum()
)