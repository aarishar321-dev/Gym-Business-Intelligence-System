import pandas as pd
from pathlib import Path


DATA_DIR = Path("data/raw")


FILES = {
    "members": DATA_DIR / "members.csv",
    "memberships": DATA_DIR / "memberships.csv",
    "attendance": DATA_DIR / "attendance.csv",
    "payments": DATA_DIR / "payments.csv",
    "leads": DATA_DIR / "leads.csv",
    "followups": DATA_DIR / "followups.csv"
}


print("Loading datasets...")


members_df = pd.read_csv(
    FILES["members"],
    parse_dates=["join_date", "created_at"]
)

memberships_df = pd.read_csv(
    FILES["memberships"],
    parse_dates=["start_date", "end_date", "created_at"]
)

attendance_df = pd.read_csv(
    FILES["attendance"],
    parse_dates=["check_in_date", "created_at"]
)

payments_df = pd.read_csv(
    FILES["payments"],
    parse_dates=["payment_date", "created_at"]
)

leads_df = pd.read_csv(
    FILES["leads"],
    parse_dates=["created_at"]
)

followups_df = pd.read_csv(
    FILES["followups"],
    parse_dates=["followup_date"]
)


errors = []


print("\nDataset row counts:")

for name, df in [
    ("Members", members_df),
    ("Memberships", memberships_df),
    ("Attendance", attendance_df),
    ("Payments", payments_df),
    ("Leads", leads_df),
    ("Follow-ups", followups_df)
]:

    print(
        f"{name}: {len(df):,}"
    )


print("\nChecking primary keys...")


if members_df["member_id"].duplicated().any():

    errors.append(
        "Duplicate member IDs found."
    )

else:

    print("Members primary key: PASS")


if memberships_df["membership_id"].duplicated().any():

    errors.append(
        "Duplicate membership IDs found."
    )

else:

    print("Memberships primary key: PASS")


if attendance_df["attendance_id"].duplicated().any():

    errors.append(
        "Duplicate attendance IDs found."
    )

else:

    print("Attendance primary key: PASS")


if payments_df["payment_id"].duplicated().any():

    errors.append(
        "Duplicate payment IDs found."
    )

else:

    print("Payments primary key: PASS")


if leads_df["lead_id"].duplicated().any():

    errors.append(
        "Duplicate lead IDs found."
    )

else:

    print("Leads primary key: PASS")


if followups_df["followup_id"].duplicated().any():

    errors.append(
        "Duplicate follow-up IDs found."
    )

else:

    print("Follow-ups primary key: PASS")


member_ids = set(
    members_df["member_id"]
)

membership_ids = set(
    memberships_df["membership_id"]
)

lead_ids = set(
    leads_df["lead_id"]
)


print("\nChecking foreign keys...")


invalid_membership_members = (
    ~memberships_df["member_id"].isin(
        member_ids
    )
).sum()

if invalid_membership_members > 0:

    errors.append(
        f"{invalid_membership_members} memberships reference invalid members."
    )

else:

    print(
        "Membership → Member: PASS"
    )


invalid_attendance_members = (
    ~attendance_df["member_id"].isin(
        member_ids
    )
).sum()

if invalid_attendance_members > 0:

    errors.append(
        f"{invalid_attendance_members} attendance records reference invalid members."
    )

else:

    print(
        "Attendance → Member: PASS"
    )


invalid_payment_members = (
    ~payments_df["member_id"].isin(
        member_ids
    )
).sum()

if invalid_payment_members > 0:

    errors.append(
        f"{invalid_payment_members} payments reference invalid members."
    )

else:

    print(
        "Payment → Member: PASS"
    )


invalid_payment_memberships = (
    ~payments_df["membership_id"].isin(
        membership_ids
    )
).sum()

if invalid_payment_memberships > 0:

    errors.append(
        f"{invalid_payment_memberships} payments reference invalid memberships."
    )

else:

    print(
        "Payment → Membership: PASS"
    )


invalid_followup_leads = (
    ~followups_df["lead_id"].isin(
        lead_ids
    )
).sum()

if invalid_followup_leads > 0:

    errors.append(
        f"{invalid_followup_leads} follow-ups reference invalid leads."
    )

else:

    print(
        "Follow-up → Lead: PASS"
    )


print("\nChecking converted lead relationships...")


converted_leads = leads_df[
    leads_df["status"] == "CONVERTED"
]


converted_without_member = (
    converted_leads["converted_member_id"]
    .isna()
).sum()


if converted_without_member > 0:

    errors.append(
        f"{converted_without_member} converted leads have no member ID."
    )

else:

    print(
        "Converted leads with member IDs: PASS"
    )


invalid_converted_members = (
    ~converted_leads["converted_member_id"].isin(
        member_ids
    )
).sum()


if invalid_converted_members > 0:

    errors.append(
        f"{invalid_converted_members} converted leads reference invalid members."
    )

else:

    print(
        "Converted Lead → Member: PASS"
    )


print("\nChecking date logic...")


membership_before_join = (
    memberships_df.merge(
        members_df[
            [
                "member_id",
                "join_date"
            ]
        ],
        on="member_id",
        how="left"
    )
)

invalid_membership_dates = (
    membership_before_join["start_date"]
    < membership_before_join["join_date"]
).sum()


if invalid_membership_dates > 0:

    errors.append(
        f"{invalid_membership_dates} memberships start before member join date."
    )

else:

    print(
        "Membership start ≥ member join date: PASS"
    )


invalid_membership_ranges = (
    memberships_df["end_date"]
    < memberships_df["start_date"]
).sum()


if invalid_membership_ranges > 0:

    errors.append(
        f"{invalid_membership_ranges} memberships have end date before start date."
    )

else:

    print(
        "Membership start/end dates: PASS"
    )


attendance_before_join = (
    attendance_df.merge(
        members_df[
            [
                "member_id",
                "join_date"
            ]
        ],
        on="member_id",
        how="left"
    )
)

invalid_attendance_join_dates = (
    attendance_before_join["check_in_date"]
    < attendance_before_join["join_date"]
).sum()


if invalid_attendance_join_dates > 0:

    errors.append(
        f"{invalid_attendance_join_dates} attendance records occur before member join date."
    )

else:

    print(
        "Attendance ≥ member join date: PASS"
    )


print("\nChecking attendance against memberships...")


attendance_memberships = attendance_df.merge(
    memberships_df[
        [
            "member_id",
            "start_date",
            "end_date"
        ]
    ],
    on="member_id",
    how="left"
)


def attendance_has_membership(row):

    matching_memberships = (
        attendance_memberships[
            (attendance_memberships["member_id"] == row["member_id"])
            & (attendance_memberships["start_date"] <= row["check_in_date"])
            & (attendance_memberships["end_date"] >= row["check_in_date"])
        ]
    )

    return len(matching_memberships) > 0


attendance_validity_sample = attendance_df.sample(
    n=min(5000, len(attendance_df)),
    random_state=42
)


attendance_check = (
    attendance_validity_sample
    .apply(
        attendance_has_membership,
        axis=1
    )
)


invalid_attendance_membership_dates = (
    (~attendance_check).sum()
)


if invalid_attendance_membership_dates > 0:

    errors.append(
        f"{invalid_attendance_membership_dates} sampled attendance records fall outside membership periods."
    )

else:

    print(
        "Attendance within membership periods: PASS"
    )


print("\nChecking payments against memberships...")


payment_memberships = payments_df.merge(
    memberships_df[
        [
            "membership_id",
            "member_id",
            "start_date",
            "end_date"
        ]
    ],
    on="membership_id",
    how="left",
    suffixes=(
        "_payment",
        "_membership"
    )
)


invalid_payment_member_links = (
    payment_memberships[
        payment_memberships["member_id_payment"]
        !=
        payment_memberships["member_id_membership"]
    ]
)


if len(invalid_payment_member_links) > 0:

    errors.append(
        f"{len(invalid_payment_member_links)} payments have member/membership mismatch."
    )

else:

    print(
        "Payment member/membership relationship: PASS"
    )


invalid_payment_dates = (
    payment_memberships[
        (payment_memberships["payment_date"] < payment_memberships["start_date"])
        |
        (payment_memberships["payment_date"] > payment_memberships["end_date"])
    ]
)


if len(invalid_payment_dates) > 0:

    errors.append(
        f"{len(invalid_payment_dates)} payments occur outside membership periods."
    )

else:

    print(
        "Payment dates within membership periods: PASS"
    )


print("\nChecking follow-up dates...")


followup_leads = followups_df.merge(
    leads_df[
        [
            "lead_id",
            "created_at"
        ]
    ],
    on="lead_id",
    how="left"
)


invalid_followup_dates = (
    followup_leads[
        followup_leads["followup_date"]
        < followup_leads["created_at"]
    ]
)


if len(invalid_followup_dates) > 0:

    errors.append(
        f"{len(invalid_followup_dates)} follow-ups occur before lead creation."
    )

else:

    print(
        "Follow-up date ≥ lead creation: PASS"
    )


print("\nChecking missing values...")


for name, df in [
    ("Members", members_df),
    ("Memberships", memberships_df),
    ("Attendance", attendance_df),
    ("Payments", payments_df),
    ("Leads", leads_df),
    ("Follow-ups", followups_df)
]:

    missing_count = int(
        df.isnull().sum().sum()
    )


    if missing_count > 0:

        print(
            f"{name}: {missing_count} missing values"
        )

    else:

        print(
            f"{name}: 0 missing values"
        )


print("\nChecking numeric values...")


negative_payment_amounts = (
    payments_df["amount"] < 0
).sum()


if negative_payment_amounts > 0:

    errors.append(
        f"{negative_payment_amounts} payments have negative amounts."
    )

else:

    print(
        "Payment amounts: PASS"
    )


negative_refunds = (
    payments_df["refund_amount"] < 0
).sum()


if negative_refunds > 0:

    errors.append(
        f"{negative_refunds} refunds have negative amounts."
    )

else:

    print(
        "Refund amounts: PASS"
    )


refund_greater_than_payment = (
    payments_df["refund_amount"]
    > payments_df["amount"]
).sum()


if refund_greater_than_payment > 0:

    errors.append(
        f"{refund_greater_than_payment} refunds exceed payment amounts."
    )

else:

    print(
        "Refund ≤ payment amount: PASS"
    )


print("\nChecking dataset coverage...")


print(
    f"Unique members: {members_df['member_id'].nunique():,}"
)

print(
    f"Unique members with memberships: "
    f"{memberships_df['member_id'].nunique():,}"
)

print(
    f"Unique members with attendance: "
    f"{attendance_df['member_id'].nunique():,}"
)

print(
    f"Unique members with payments: "
    f"{payments_df['member_id'].nunique():,}"
)

print(
    f"Unique leads: {leads_df['lead_id'].nunique():,}"
)

print(
    f"Unique leads with follow-ups: "
    f"{followups_df['lead_id'].nunique():,}"
)


print("\nValidation summary")


if len(errors) == 0:

    print(
        "ALL CROSS-TABLE VALIDATIONS PASSED!"
    )

    print(
        "The clean synthetic dataset is ready."
    )

else:

    print(
        f"VALIDATION FAILED: {len(errors)} issue(s) found."
    )

    print("\nIssues:")

    for error in errors:

        print(
            f"- {error}"
        )