import pandas as pd
import numpy as np
from pathlib import Path

#1.Configuration

SEED = 42

np.random.seed(SEED)


#2.File Path

INPUT_FILE = Path("data/raw/members.csv")
OUTPUT_DIR = Path("data/raw")

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


#3. Reference data

PLANS = {
    "Monthly": {
        "duration_days": 30,
        "price": 1200
    },

    "Quarterly": {
        "duration_days": 90,
        "price": 3000
    },

    "Half-Yearly": {
        "duration_days": 180,
        "price": 5000
    },

    "Yearly": {
        "duration_days": 365,
        "price": 9000
    }
}


PLAN_NAMES = list(PLANS.keys())


#4.load members

members_df = pd.read_csv(
    INPUT_FILE,
    parse_dates=["join_date"]
)


#5.Current date

today = pd.Timestamp.today().normalize()


#6.Generate memberships

memberships = []

membership_counter = 1


for _, member in members_df.iterrows():

    member_id = member["member_id"]

    current_start_date = member["join_date"]

    #Decide max number of memberships

    max_memberships = np.random.choice(
        [1, 2, 3, 4],
        p=[0.50, 0.30, 0.15, 0.05]
    )


    # Generate membership history

    for membership_number in range(max_memberships):

        # Don't create a future membership
        if current_start_date > today:
            break

        # Choose membership plan
        plan = np.random.choice(
            PLAN_NAMES,
            p=[0.45, 0.30, 0.15, 0.10]
        )


        duration_days = PLANS[plan]["duration_days"]

        price = PLANS[plan]["price"]

        # Calculate end date
        end_date = (
            current_start_date
            + pd.Timedelta(days=duration_days)
        )

        #Determine end status
        if end_date >= today:

            # Current membership
            status = "ACTIVE"


        else:

            # Membership has ended
            status = np.random.choice(
                ["EXPIRED", "CANCELLED"],
                p=[0.90, 0.10]
            )

        # Create membership records

        memberships.append({

            "membership_id":
                f"MS{membership_counter:05d}",

            "member_id":
                member_id,

            "plan":
                plan,

            "start_date":
                current_start_date,

            "end_date":
                end_date,

            "price":
                price,

            "status":
                status,

            "created_at":
                current_start_date

        })


        membership_counter += 1

        # If current membership is active,
        # there cannot be another membership yet

        if status == "ACTIVE":
            break

        # Decide whether member renews
        renews = np.random.choice(
            [True, False],
            p=[0.65, 0.35]
        )


        if not renews:
            break

        # Renewal gap
        renewal_gap = np.random.choice(
            [0, 1, 3, 7, 14],
            p=[0.45, 0.20, 0.15, 0.10, 0.10]
        )

        # Start next membership
        current_start_date = (
            end_date
            + pd.Timedelta(days=renewal_gap + 1)
        )


# 7. Create dataframe

memberships_df = pd.DataFrame(
    memberships
)

# 8. Save data

output_file = (
    OUTPUT_DIR / "memberships.csv"
)

memberships_df.to_csv(
    output_file,
    index=False
)

# 9. Basic validation

print(
    "Membership dataset generated successfully!"
)

print(
    f"Rows: {len(memberships_df)}"
)

print(
    f"Columns: {len(memberships_df.columns)}"
)

print(
    f"Saved to: {output_file}"
)

print("\nFirst 5 rows:")

print(
    memberships_df.head()
)
print("\nMemberships per member:")

print(
    memberships_df["member_id"]
    .value_counts()
    .describe()
)

print("\nPlan distribution:")

print(
    memberships_df["plan"]
    .value_counts()
)

print("\nStatus distribution:")

print(
    memberships_df["status"]
    .value_counts()
)
print("\nDuplicate membership IDs:")

print(
    memberships_df["membership_id"]
    .duplicated()
    .sum()
)
print("\nFuture memberships:")

print(
    (
        memberships_df["start_date"] > today
    ).sum()
)
print("\nActive memberships ending in the future:")

print(
    (
        (memberships_df["status"] == "ACTIVE")
        &
        (memberships_df["end_date"] >= today)
    ).sum()
)
print("\nMembers with multiple memberships:")

print(
    (
        memberships_df["member_id"]
        .value_counts() > 1
    ).sum()
)