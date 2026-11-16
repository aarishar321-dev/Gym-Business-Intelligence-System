import pandas as pd
import numpy as np
from pathlib import Path


SEED = 42

np.random.seed(SEED)


RAW_DIR = Path("data/raw")
MESSY_DIR = Path("data/messy")

MESSY_DIR.mkdir(
    parents=True,
    exist_ok=True
)


FILES = [
    "members.csv",
    "memberships.csv",
    "attendance.csv",
    "payments.csv",
    "leads.csv",
    "followups.csv"
]


print("Creating messy datasets...")


for file_name in FILES:

    source_file = RAW_DIR / file_name

    output_file = MESSY_DIR / file_name


    df = pd.read_csv(
        source_file
    )


    original_rows = len(df)


    if file_name == "members.csv":

        indices = np.random.choice(
            df.index,
            size=40,
            replace=False
        )


        df.loc[
            indices[:10],
            "name"
        ] = (
            df.loc[
                indices[:10],
                "name"
            ]
            .astype(str)
            .str.lower()
        )


        df.loc[
            indices[10:20],
            "name"
        ] = (
            df.loc[
                indices[10:20],
                "name"
            ]
            .astype(str)
            .str.upper()
        )


        df.loc[
            indices[20:30],
            "phone"
        ] = (
            df.loc[
                indices[20:30],
                "phone"
            ]
            .astype(str)
            .str.replace(
                "+91",
                "",
                regex=False
            )
        )


        df.loc[
            indices[30:40],
            "acquisition_source"
        ] = (
            df.loc[
                indices[30:40],
                "acquisition_source"
            ]
            .astype(str)
            .str.lower()
        )


        missing_indices = np.random.choice(
            df.index,
            size=15,
            replace=False
        )


        df.loc[
            missing_indices,
            "date_of_birth"
        ] = np.nan


        whitespace_indices = np.random.choice(
            df.index,
            size=20,
            replace=False
        )


        df.loc[
            whitespace_indices,
            "name"
        ] = (
            "  "
            + df.loc[
                whitespace_indices,
                "name"
            ]
            .astype(str)
            + "  "
        )


    elif file_name == "memberships.csv":

        indices = np.random.choice(
            df.index,
            size=50,
            replace=False
        )


        df.loc[
            indices[:15],
            "plan"
        ] = (
            df.loc[
                indices[:15],
                "plan"
            ]
            .astype(str)
            .str.lower()
        )


        df.loc[
            indices[15:30],
            "plan"
        ] = (
            " "
            + df.loc[
                indices[15:30],
                "plan"
            ]
            .astype(str)
            + " "
        )


        df.loc[
            indices[30:40],
            "status"
        ] = (
            df.loc[
                indices[30:40],
                "status"
            ]
            .astype(str)
            .str.lower()
        )


        df.loc[
            indices[40:50],
            "price"
        ] = (
            "₹"
            + df.loc[
                indices[40:50],
                "price"
            ]
            .astype(str)
        )


        missing_indices = np.random.choice(
            df.index,
            size=10,
            replace=False
        )


        df.loc[
            missing_indices,
            "price"
        ] = np.nan


        date_indices = np.random.choice(
            df.index,
            size=15,
            replace=False
        )


        df.loc[
            date_indices,
            "start_date"
        ] = (
            pd.to_datetime(
                df.loc[
                    date_indices,
                    "start_date"
                ]
            )
            .dt.strftime("%d/%m/%Y")
        )


    elif file_name == "attendance.csv":

        indices = np.random.choice(
            df.index,
            size=80,
            replace=False
        )


        df.loc[
            indices[:20],
            "session_type"
        ] = (
            df.loc[
                indices[:20],
                "session_type"
            ]
            .astype(str)
            .str.lower()
        )


        df.loc[
            indices[20:40],
            "session_type"
        ] = (
            " "
            + df.loc[
                indices[20:40],
                "session_type"
            ]
            .astype(str)
            + " "
        )


        df.loc[
            indices[40:60],
            "session_duration"
        ] = (
            df.loc[
                indices[40:60],
                "session_duration"
            ]
            .astype(str)
        )


        missing_indices = np.random.choice(
            df.index,
            size=20,
            replace=False
        )


        df.loc[
            missing_indices,
            "session_duration"
        ] = np.nan


        duplicate_rows = df.sample(
            n=25,
            random_state=SEED
        )


        df = pd.concat(
            [
                df,
                duplicate_rows
            ],
            ignore_index=True
        )


    elif file_name == "payments.csv":

        indices = np.random.choice(
            df.index,
            size=60,
            replace=False
        )


        df.loc[
            indices[:15],
            "payment_method"
        ] = (
            df.loc[
                indices[:15],
                "payment_method"
            ]
            .astype(str)
            .str.lower()
        )


        df.loc[
            indices[15:30],
            "payment_method"
        ] = (
            " "
            + df.loc[
                indices[15:30],
                "payment_method"
            ]
            .astype(str)
            + " "
        )


        df.loc[
            indices[30:40],
            "payment_status"
        ] = (
            df.loc[
                indices[30:40],
                "payment_status"
            ]
            .astype(str)
            .str.lower()
        )


        df.loc[
            indices[40:50],
            "amount"
        ] = (
            "₹"
            + df.loc[
                indices[40:50],
                "amount"
            ]
            .astype(str)
        )


        df.loc[
            indices[50:60],
            "refund_amount"
        ] = (
            df.loc[
                indices[50:60],
                "refund_amount"
            ]
            .astype(str)
        )


        missing_indices = np.random.choice(
            df.index,
            size=12,
            replace=False
        )


        df.loc[
            missing_indices,
            "payment_method"
        ] = np.nan


        duplicate_rows = df.sample(
            n=15,
            random_state=SEED
        )


        df = pd.concat(
            [
                df,
                duplicate_rows
            ],
            ignore_index=True
        )


    elif file_name == "leads.csv":

        indices = np.random.choice(
            df.index,
            size=60,
            replace=False
        )


        df.loc[
            indices[:15],
            "source"
        ] = (
            df.loc[
                indices[:15],
                "source"
            ]
            .astype(str)
            .str.lower()
        )


        df.loc[
            indices[15:30],
            "status"
        ] = (
            df.loc[
                indices[15:30],
                "status"
            ]
            .astype(str)
            .str.lower()
        )


        df.loc[
            indices[30:45],
            "interested_plan"
        ] = (
            " "
            + df.loc[
                indices[30:45],
                "interested_plan"
            ]
            .astype(str)
            + " "
        )


        df.loc[
            indices[45:60],
            "phone"
        ] = (
            df.loc[
                indices[45:60],
                "phone"
            ]
            .astype(str)
            .str.replace(
                "+91",
                "",
                regex=False
            )
        )


        missing_name_indices = np.random.choice(
            df.index,
            size=12,
            replace=False
        )


        df.loc[
            missing_name_indices,
            "name"
        ] = np.nan


        duplicate_rows = df.sample(
            n=20,
            random_state=SEED
        )


        df = pd.concat(
            [
                df,
                duplicate_rows
            ],
            ignore_index=True
        )


    elif file_name == "followups.csv":

        indices = np.random.choice(
            df.index,
            size=50,
            replace=False
        )


        df.loc[
            indices[:15],
            "followup_type"
        ] = (
            df.loc[
                indices[:15],
                "followup_type"
            ]
            .astype(str)
            .str.lower()
        )


        df.loc[
            indices[15:30],
            "status"
        ] = (
            df.loc[
                indices[15:30],
                "status"
            ]
            .astype(str)
            .str.lower()
        )


        df.loc[
            indices[30:40],
            "outcome"
        ] = (
            " "
            + df.loc[
                indices[30:40],
                "outcome"
            ]
            .astype(str)
            + " "
        )


        missing_indices = np.random.choice(
            df.index,
            size=10,
            replace=False
        )


        df.loc[
            missing_indices,
            "outcome"
        ] = np.nan


        duplicate_rows = df.sample(
            n=15,
            random_state=SEED
        )


        df = pd.concat(
            [
                df,
                duplicate_rows
            ],
            ignore_index=True
        )


    df.to_csv(
        output_file,
        index=False
    )


    print(
        f"{file_name}: "
        f"{original_rows:,} → "
        f"{len(df):,} rows"
    )


print("\nMessy datasets created successfully!")

print(
    f"Saved to: {MESSY_DIR}"
)


print("\nFiles created:")

for file_name in FILES:

    output_file = (
        MESSY_DIR / file_name
    )

    print(
        f"- {output_file}"
    )