import pandas as pd
import numpy as np
from pathlib import Path


SEED = 42

np.random.seed(SEED)


MEMBERS_FILE = Path("data/raw/members.csv")
MEMBERSHIPS_FILE = Path("data/raw/memberships.csv")
OUTPUT_DIR = Path("data/raw")

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


members_df = pd.read_csv(
    MEMBERS_FILE,
    parse_dates=["join_date"]
)

memberships_df = pd.read_csv(
    MEMBERSHIPS_FILE,
    parse_dates=["start_date", "end_date"]
)


today = pd.Timestamp.today().normalize()


attendance_records = []

attendance_counter = 1


attendance_types = [
    "Strength Training",
    "Cardio",
    "Personal Training",
    "Group Class",
    "Mixed Workout"
]

attendance_type_probabilities = [
    0.40,
    0.20,
    0.15,
    0.10,
    0.15
]


day_probabilities = {
    0: 0.90,
    1: 1.00,
    2: 1.00,
    3: 1.00,
    4: 0.95,
    5: 0.85,
    6: 0.65
}


member_profiles = {}


for member_id in members_df["member_id"]:

    profile_type = np.random.choice(
        [
            "HIGH",
            "MEDIUM",
            "LOW"
        ],
        p=[
            0.25,
            0.55,
            0.20
        ]
    )

    if profile_type == "HIGH":

        base_probability = np.random.uniform(
            0.35,
            0.48
        )

    elif profile_type == "MEDIUM":

        base_probability = np.random.uniform(
            0.22,
            0.34
        )

    else:

        base_probability = np.random.uniform(
            0.12,
            0.21
        )

    declining_behavior = np.random.choice(
        [True, False],
        p=[0.25, 0.75]
    )

    member_profiles[member_id] = {
        "profile_type": profile_type,
        "base_probability": base_probability,
        "declining_behavior": declining_behavior
    }


for _, membership in memberships_df.iterrows():

    member_id = membership["member_id"]

    start_date = membership["start_date"]

    end_date = membership["end_date"]

    if start_date > today:
        continue

    actual_end_date = min(
        end_date,
        today
    )

    if actual_end_date < start_date:
        continue


    profile = member_profiles[member_id]

    base_probability = profile["base_probability"]

    declining_behavior = profile["declining_behavior"]


    date_range = pd.date_range(
        start=start_date,
        end=actual_end_date,
        freq="D"
    )


    for current_date in date_range:

        days_from_start = (
            current_date - start_date
        ).days

        membership_length = (
            actual_end_date - start_date
        ).days


        probability = base_probability


        if declining_behavior and membership_length > 90:

            remaining_days = (
                actual_end_date - current_date
            ).days

            if remaining_days <= 60:

                decline_factor = (
                    remaining_days / 60
                )

                probability *= (
                    0.45
                    + 0.55 * decline_factor
                )


        weekday = current_date.weekday()

        probability *= day_probabilities[weekday]


        probability = min(
            max(probability, 0.02),
            0.60
        )


        if np.random.random() > probability:
            continue


        session_duration = np.random.choice(
            [
                30,
                45,
                60,
                75,
                90,
                120
            ],
            p=[
                0.05,
                0.15,
                0.35,
                0.20,
                0.20,
                0.05
            ]
        )


        session_type = np.random.choice(
            attendance_types,
            p=attendance_type_probabilities
        )


        hour = np.random.choice(
            [
                5,
                6,
                7,
                8,
                9,
                10,
                16,
                17,
                18,
                19,
                20,
                21
            ],
            p=[
                0.03,
                0.06,
                0.10,
                0.07,
                0.05,
                0.04,
                0.05,
                0.10,
                0.15,
                0.18,
                0.12,
                0.05
            ]
        )


        minute = np.random.randint(
            0,
            60
        )


        second = np.random.randint(
            0,
            60
        )


        check_in_time = (
            f"{hour:02d}:"
            f"{minute:02d}:"
            f"{second:02d}"
        )


        created_at = (
            current_date
            + pd.Timedelta(
                hours=int(hour),
                minutes=int(minute),
                seconds=int(second)
            )
        )


        attendance_records.append({
            "attendance_id": attendance_counter,
            "member_id": member_id,
            "check_in_date": current_date.date(),
            "check_in_time": check_in_time,
            "session_duration": session_duration,
            "session_type": session_type,
            "created_at": created_at
        })


        attendance_counter += 1


attendance_df = pd.DataFrame(
    attendance_records
)


output_file = (
    OUTPUT_DIR / "attendance.csv"
)


attendance_df.to_csv(
    output_file,
    index=False
)


print("Attendance dataset generated successfully!")

print(f"Rows: {len(attendance_df)}")

print(f"Columns: {len(attendance_df.columns)}")

print(f"Saved to: {output_file}")


print("\nFirst 10 rows:")

print(
    attendance_df.head(10)
)


print("\nMissing values:")

print(
    attendance_df.isnull().sum()
)


print("\nDuplicate attendance IDs:")

print(
    attendance_df["attendance_id"]
    .duplicated()
    .sum()
)


print("\nDuplicate member/date combinations:")

duplicate_member_dates = (
    attendance_df
    .duplicated(
        subset=[
            "member_id",
            "check_in_date"
        ]
    )
    .sum()
)

print(
    duplicate_member_dates
)


print("\nAttendance date range:")

print(
    attendance_df["check_in_date"].min(),
    "to",
    attendance_df["check_in_date"].max()
)


print("\nSession type distribution:")

print(
    attendance_df["session_type"]
    .value_counts()
)


print("\nSession duration distribution:")

print(
    attendance_df["session_duration"]
    .value_counts()
    .sort_index()
)


print("\nAttendance records per member:")

attendance_per_member = (
    attendance_df
    .groupby("member_id")
    .size()
)

print(
    attendance_per_member.describe()
)


print("\nMembers with attendance:")

print(
    attendance_df["member_id"].nunique()
)


print("\nMembers without attendance:")

print(
    len(members_df)
    - attendance_df["member_id"].nunique()
)