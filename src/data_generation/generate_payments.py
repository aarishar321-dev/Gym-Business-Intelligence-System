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


payment_methods = [
    "UPI",
    "Cash",
    "Card",
    "Net Banking"
]

payment_method_probabilities = [
    0.45,
    0.20,
    0.25,
    0.10
]


payment_records = []

payment_counter = 1


for _, membership in memberships_df.iterrows():

    membership_id = membership["membership_id"]

    member_id = membership["member_id"]

    start_date = membership["start_date"]

    end_date = membership["end_date"]

    amount = float(membership["price"])


    if start_date > today:
        continue


    payment_date = start_date


    payment_status_random = np.random.random()


    if payment_status_random < 0.94:

        payment_status = "SUCCESS"

    elif payment_status_random < 0.98:

        payment_status = "FAILED"

    else:

        payment_status = "PENDING"


    payment_method = np.random.choice(
        payment_methods,
        p=payment_method_probabilities
    )


    refund_amount = 0.0


    if payment_status == "SUCCESS":

        refund_probability = 0.04

        if np.random.random() < refund_probability:

            refund_percentage = np.random.choice(
                [0.25, 0.50, 1.00],
                p=[0.50, 0.35, 0.15]
            )

            refund_amount = round(
                amount * refund_percentage,
                2
            )


    created_at = (
        payment_date
        + pd.Timedelta(
            hours=np.random.randint(8, 21),
            minutes=np.random.randint(0, 60),
            seconds=np.random.randint(0, 60)
        )
    )


    payment_records.append({
        "payment_id": f"PAY{payment_counter:05d}",
        "member_id": member_id,
        "membership_id": membership_id,
        "payment_date": payment_date.date(),
        "amount": amount,
        "payment_method": payment_method,
        "payment_status": payment_status,
        "refund_amount": refund_amount,
        "created_at": created_at
    })


    payment_counter += 1


payments_df = pd.DataFrame(
    payment_records
)


output_file = (
    OUTPUT_DIR / "payments.csv"
)


payments_df.to_csv(
    output_file,
    index=False
)


print("Payment dataset generated successfully!")

print(f"Rows: {len(payments_df)}")

print(f"Columns: {len(payments_df.columns)}")

print(f"Saved to: {output_file}")


print("\nFirst 10 rows:")

print(
    payments_df.head(10)
)


print("\nMissing values:")

print(
    payments_df.isnull().sum()
)


print("\nDuplicate payment IDs:")

print(
    payments_df["payment_id"]
    .duplicated()
    .sum()
)


print("\nPayment status distribution:")

print(
    payments_df["payment_status"]
    .value_counts()
)


print("\nPayment method distribution:")

print(
    payments_df["payment_method"]
    .value_counts()
)


print("\nRefund summary:")

print(
    f"Transactions with refunds: "
    f"{(payments_df['refund_amount'] > 0).sum()}"
)

print(
    f"Total refund amount: "
    f"₹{payments_df['refund_amount'].sum():,.2f}"
)


successful_payments = (
    payments_df[
        payments_df["payment_status"] == "SUCCESS"
    ]
)


net_revenue = (
    successful_payments["amount"].sum()
    - successful_payments["refund_amount"].sum()
)


print("\nRevenue summary:")

print(
    f"Gross successful payment amount: "
    f"₹{successful_payments['amount'].sum():,.2f}"
)

print(
    f"Net revenue after refunds: "
    f"₹{net_revenue:,.2f}"
)


print("\nPayment date range:")

print(
    payments_df["payment_date"].min(),
    "to",
    payments_df["payment_date"].max()
)


print("\nMemberships with payments:")

print(
    payments_df["membership_id"].nunique()
)


print("\nMemberships without payments:")

print(
    len(memberships_df)
    - payments_df["membership_id"].nunique()
)


print("\nForeign key validation:")

invalid_members = (
    ~payments_df["member_id"].isin(
        members_df["member_id"]
    )
).sum()

invalid_memberships = (
    ~payments_df["membership_id"].isin(
        memberships_df["membership_id"]
    )
).sum()

print(
    f"Invalid member IDs: {invalid_members}"
)

print(
    f"Invalid membership IDs: {invalid_memberships}"
)


print("\nAmount validation:")

print(
    f"Negative amounts: "
    f"{(payments_df['amount'] < 0).sum()}"
)

print(
    f"Refunds greater than payment amount: "
    f"{(payments_df['refund_amount'] > payments_df['amount']).sum()}"
)