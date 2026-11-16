import pandas as pd
import numpy as np
from pathlib import Path


DATA_DIR = Path("data/messy")
REPORT_DIR = Path("data/processed")

REPORT_DIR.mkdir(
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


ALLOWED_VALUES = {
    "members": {
        "gender": {
            "Male",
            "Female",
            "Other"
        },
        "acquisition_source": {
            "WhatsApp",
            "Instagram",
            "Google",
            "Referral",
            "Walk-in",
            "Website"
        }
    },
    "memberships": {
        "plan": {
            "Monthly",
            "Quarterly",
            "Half-Yearly",
            "Yearly"
        },
        "status": {
            "ACTIVE",
            "EXPIRED",
            "CANCELLED"
        }
    },
    "attendance": {
        "session_type": {
            "Strength Training",
            "Cardio",
            "Personal Training",
            "Mixed Workout",
            "Group Class"
        }
    },
    "payments": {
        "payment_method": {
            "UPI",
            "Card",
            "Cash",
            "Net Banking"
        },
        "payment_status": {
            "SUCCESS",
            "FAILED",
            "PENDING"
        }
    },
    "leads": {
        "source": {
            "WhatsApp",
            "Instagram",
            "Google",
            "Referral",
            "Walk-in",
            "Website"
        },
        "interested_plan": {
            "Monthly",
            "Quarterly",
            "Half-Yearly",
            "Yearly"
        },
        "status": {
            "NEW",
            "QUALIFIED",
            "FOLLOW_UP",
            "CONVERTED",
            "LOST",
            "NOT_INTERESTED"
        }
    },
    "followups": {
        "followup_type": {
            "WhatsApp",
            "Phone Call",
            "SMS"
        },
        "status": {
            "COMPLETED",
            "SKIPPED",
            "PENDING"
        }
    }
}


REQUIRED_COLUMNS = {
    "members": [
        "member_id",
        "name",
        "phone",
        "join_date",
        "acquisition_source"
    ],
    "memberships": [
        "membership_id",
        "member_id",
        "plan",
        "start_date",
        "end_date",
        "price",
        "status"
    ],
    "attendance": [
        "attendance_id",
        "member_id",
        "check_in_date",
        "check_in_time",
        "session_duration",
        "session_type"
    ],
    "payments": [
        "payment_id",
        "member_id",
        "membership_id",
        "payment_date",
        "amount",
        "payment_method",
        "payment_status",
        "refund_amount"
    ],
    "leads": [
        "lead_id",
        "name",
        "phone",
        "created_at",
        "source",
        "interested_plan",
        "status"
    ],
    "followups": [
        "followup_id",
        "lead_id",
        "followup_date",
        "followup_type",
        "status",
        "outcome"
    ]
}


PRIMARY_KEYS = {
    "members": "member_id",
    "memberships": "membership_id",
    "attendance": "attendance_id",
    "payments": "payment_id",
    "leads": "lead_id",
    "followups": "followup_id"
}


results = []


def add_result(
    dataset,
    check,
    issue_count,
    severity,
    details
):

    results.append({
        "dataset": dataset,
        "check": check,
        "issue_count": int(issue_count),
        "severity": severity,
        "details": details
    })


def check_required_columns(
    dataset,
    df
):

    required = REQUIRED_COLUMNS[dataset]

    missing_columns = [
        column
        for column in required
        if column not in df.columns
    ]

    add_result(
        dataset,
        "Required columns",
        len(missing_columns),
        "CRITICAL" if missing_columns else "PASS",
        (
            ", ".join(missing_columns)
            if missing_columns
            else "All required columns present"
        )
    )


def check_missing_values(
    dataset,
    df
):

    for column in df.columns:

        missing_count = int(
            df[column].isna().sum()
        )

        if missing_count > 0:

            if (
                dataset == "leads"
                and column == "converted_member_id"
            ):

                severity = "INFO"

                details = (
                    "Expected for non-converted leads"
                )

            else:

                severity = "WARNING"

                details = (
                    f"{missing_count} missing values"
                )

            add_result(
                dataset,
                f"Missing values: {column}",
                missing_count,
                severity,
                details
            )


def check_duplicate_primary_key(
    dataset,
    df
):

    primary_key = PRIMARY_KEYS[dataset]

    if primary_key not in df.columns:

        return

    duplicate_count = int(
        df[primary_key]
        .duplicated()
        .sum()
    )

    add_result(
        dataset,
        f"Duplicate primary key: {primary_key}",
        duplicate_count,
        "CRITICAL" if duplicate_count > 0 else "PASS",
        (
            f"{duplicate_count} duplicate values"
            if duplicate_count > 0
            else "No duplicate primary keys"
        )
    )


def check_whitespace(
    dataset,
    df
):

    for column in df.select_dtypes(
        include=["object"]
    ).columns:

        series = (
            df[column]
            .dropna()
            .astype(str)
        )

        whitespace_count = int(
            series.str.contains(
                r"^\s|\s$",
                regex=True
            ).sum()
        )

        if whitespace_count > 0:

            add_result(
                dataset,
                f"Leading/trailing whitespace: {column}",
                whitespace_count,
                "WARNING",
                "Values contain unnecessary spaces"
            )


def check_case_inconsistency(
    dataset,
    df
):

    for column in df.select_dtypes(
        include=["object"]
    ).columns:

        series = (
            df[column]
            .dropna()
            .astype(str)
        )

        normalized = (
            series
            .str.strip()
            .str.lower()
        )

        grouped = pd.DataFrame({
            "original": series,
            "normalized": normalized
        })

        inconsistent_count = 0

        for _, group in grouped.groupby(
            "normalized"
        ):

            if group["original"].nunique() > 1:

                inconsistent_count += len(group)


        if inconsistent_count > 0:

            add_result(
                dataset,
                f"Case inconsistency: {column}",
                inconsistent_count,
                "WARNING",
                "Multiple representations of the same value detected"
            )


def check_allowed_values(
    dataset,
    df
):

    if dataset not in ALLOWED_VALUES:

        return


    for column, allowed in ALLOWED_VALUES[
        dataset
    ].items():

        if column not in df.columns:

            continue


        series = (
            df[column]
            .dropna()
            .astype(str)
            .str.strip()
        )


        invalid_mask = ~series.isin(
            allowed
        )

        invalid_count = int(
            invalid_mask.sum()
        )


        if invalid_count > 0:

            invalid_values = sorted(
                series[invalid_mask]
                .unique()
                .tolist()
            )


            add_result(
                dataset,
                f"Invalid categorical values: {column}",
                invalid_count,
                "WARNING",
                f"Invalid values: {invalid_values}"
            )


def check_phone_numbers(
    dataset,
    df
):

    if "phone" not in df.columns:

        return


    phone_series = (
        df["phone"]
        .dropna()
        .astype(str)
        .str.strip()
    )


    valid_phone_pattern = (
        phone_series
        .str.fullmatch(
            r"\+91[6-9]\d{9}"
        )
    )


    invalid_count = int(
        (~valid_phone_pattern).sum()
    )


    add_result(
        dataset,
        "Phone format",
        invalid_count,
        "WARNING" if invalid_count > 0 else "PASS",
        (
            f"{invalid_count} invalid phone numbers"
            if invalid_count > 0
            else "All phone numbers match expected format"
        )
    )


def check_duplicate_phones(
    dataset,
    df
):

    if "phone" not in df.columns:

        return


    phone_series = (
        df["phone"]
        .dropna()
        .astype(str)
        .str.strip()
    )


    duplicate_count = int(
        phone_series
        .duplicated()
        .sum()
    )


    add_result(
        dataset,
        "Duplicate phone numbers",
        duplicate_count,
        "WARNING" if duplicate_count > 0 else "PASS",
        (
            f"{duplicate_count} duplicate phone values"
            if duplicate_count > 0
            else "No duplicate phone numbers"
        )
    )


def check_numeric_columns(
    dataset,
    df
):

    numeric_columns = {
        "memberships": [
            "price"
        ],
        "attendance": [
            "session_duration"
        ],
        "payments": [
            "amount",
            "refund_amount"
        ]
    }


    if dataset not in numeric_columns:

        return


    for column in numeric_columns[dataset]:

        if column not in df.columns:

            continue


        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce"
        )


        invalid_count = int(
            (
                df[column].notna()
                &
                numeric_values.isna()
            ).sum()
        )


        add_result(
            dataset,
            f"Numeric validity: {column}",
            invalid_count,
            "WARNING" if invalid_count > 0 else "PASS",
            (
                f"{invalid_count} non-numeric values"
                if invalid_count > 0
                else "Values are numeric"
            )
        )


def check_negative_values(
    dataset,
    df
):

    numeric_columns = []

    if dataset == "memberships":

        numeric_columns = [
            "price"
        ]

    elif dataset == "attendance":

        numeric_columns = [
            "session_duration"
        ]

    elif dataset == "payments":

        numeric_columns = [
            "amount",
            "refund_amount"
        ]


    for column in numeric_columns:

        if column not in df.columns:

            continue


        values = pd.to_numeric(
            df[column],
            errors="coerce"
        )


        negative_count = int(
            (values < 0).sum()
        )


        add_result(
            dataset,
            f"Negative values: {column}",
            negative_count,
            "WARNING" if negative_count > 0 else "PASS",
            (
                f"{negative_count} negative values"
                if negative_count > 0
                else "No negative values"
            )
        )


def check_refunds(
    df
):

    if (
        "refund_amount" not in df.columns
        or "amount" not in df.columns
    ):

        return


    amount = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    refund = pd.to_numeric(
        df["refund_amount"],
        errors="coerce"
    )


    invalid_count = int(
        (refund > amount).sum()
    )


    add_result(
        "payments",
        "Refund does not exceed payment",
        invalid_count,
        "WARNING" if invalid_count > 0 else "PASS",
        (
            f"{invalid_count} refunds exceed payment amounts"
            if invalid_count > 0
            else "All refunds are within payment amounts"
        )
    )


def check_date_columns(
    dataset,
    df
):

    date_columns = {
        "members": [
            "date_of_birth",
            "join_date",
            "created_at"
        ],
        "memberships": [
            "start_date",
            "end_date",
            "created_at"
        ],
        "attendance": [
            "check_in_date",
            "created_at"
        ],
        "payments": [
            "payment_date",
            "created_at"
        ],
        "leads": [
            "created_at"
        ],
        "followups": [
            "followup_date"
        ]
    }


    for column in date_columns[dataset]:

        if column not in df.columns:

            continue


        converted = pd.to_datetime(
            df[column],
            errors="coerce",
            dayfirst=True
        )


        invalid_count = int(
            (
                df[column].notna()
                &
                converted.isna()
            ).sum()
        )


        add_result(
            dataset,
            f"Date validity: {column}",
            invalid_count,
            "WARNING" if invalid_count > 0 else "PASS",
            (
                f"{invalid_count} invalid dates"
                if invalid_count > 0
                else "Date values are valid"
            )
        )


def check_membership_dates(
    df
):

    if not all(
        column in df.columns
        for column in [
            "start_date",
            "end_date"
        ]
    ):

        return


    start = pd.to_datetime(
        df["start_date"],
        errors="coerce",
        dayfirst=True
    )

    end = pd.to_datetime(
        df["end_date"],
        errors="coerce",
        dayfirst=True
    )


    invalid_count = int(
        (end < start).sum()
    )


    add_result(
        "memberships",
        "Membership end date ≥ start date",
        invalid_count,
        "WARNING" if invalid_count > 0 else "PASS",
        (
            f"{invalid_count} invalid membership date ranges"
            if invalid_count > 0
            else "All membership date ranges are valid"
        )
    )


def check_attendance_duration(
    df
):

    if "session_duration" not in df.columns:

        return


    duration = pd.to_numeric(
        df["session_duration"],
        errors="coerce"
    )


    invalid_count = int(
        (
            (duration < 15)
            |
            (duration > 240)
        ).sum()
    )


    add_result(
        "attendance",
        "Session duration range",
        invalid_count,
        "WARNING" if invalid_count > 0 else "PASS",
        (
            f"{invalid_count} durations outside 15–240 minutes"
            if invalid_count > 0
            else "All session durations are within expected range"
        )
    )


def check_cross_table_relationships(
    members_df,
    memberships_df,
    attendance_df,
    payments_df,
    leads_df,
    followups_df
):

    member_ids = set(
        members_df["member_id"]
        .dropna()
        .astype(str)
    )


    membership_ids = set(
        memberships_df["membership_id"]
        .dropna()
        .astype(str)
    )


    lead_ids = set(
        leads_df["lead_id"]
        .dropna()
        .astype(str)
    )


    invalid_membership_members = int(
        (
            ~memberships_df["member_id"]
            .astype(str)
            .isin(member_ids)
        ).sum()
    )


    add_result(
        "memberships",
        "Member foreign keys",
        invalid_membership_members,
        "CRITICAL" if invalid_membership_members > 0 else "PASS",
        (
            f"{invalid_membership_members} invalid member IDs"
            if invalid_membership_members > 0
            else "All member IDs exist"
        )
    )


    invalid_attendance_members = int(
        (
            ~attendance_df["member_id"]
            .astype(str)
            .isin(member_ids)
        ).sum()
    )


    add_result(
        "attendance",
        "Member foreign keys",
        invalid_attendance_members,
        "CRITICAL" if invalid_attendance_members > 0 else "PASS",
        (
            f"{invalid_attendance_members} invalid member IDs"
            if invalid_attendance_members > 0
            else "All member IDs exist"
        )
    )


    invalid_payment_members = int(
        (
            ~payments_df["member_id"]
            .astype(str)
            .isin(member_ids)
        ).sum()
    )


    add_result(
        "payments",
        "Member foreign keys",
        invalid_payment_members,
        "CRITICAL" if invalid_payment_members > 0 else "PASS",
        (
            f"{invalid_payment_members} invalid member IDs"
            if invalid_payment_members > 0
            else "All member IDs exist"
        )
    )


    invalid_payment_memberships = int(
        (
            ~payments_df["membership_id"]
            .astype(str)
            .isin(membership_ids)
        ).sum()
    )


    add_result(
        "payments",
        "Membership foreign keys",
        invalid_payment_memberships,
        "CRITICAL" if invalid_payment_memberships > 0 else "PASS",
        (
            f"{invalid_payment_memberships} invalid membership IDs"
            if invalid_payment_memberships > 0
            else "All membership IDs exist"
        )
    )


    invalid_followup_leads = int(
        (
            ~followups_df["lead_id"]
            .astype(str)
            .isin(lead_ids)
        ).sum()
    )


    add_result(
        "followups",
        "Lead foreign keys",
        invalid_followup_leads,
        "CRITICAL" if invalid_followup_leads > 0 else "PASS",
        (
            f"{invalid_followup_leads} invalid lead IDs"
            if invalid_followup_leads > 0
            else "All lead IDs exist"
        )
    )


def load_datasets():

    datasets = {}


    for file_name in FILES:

        dataset_name = Path(
            file_name
        ).stem

        file_path = DATA_DIR / file_name


        datasets[dataset_name] = pd.read_csv(
            file_path
        )


    return datasets


print("Loading messy datasets...")


datasets = load_datasets()


print("\nDataset row counts:")


for name, df in datasets.items():

    print(
        f"{name}: {len(df):,}"
    )


for dataset_name, df in datasets.items():

    print(
        f"\nValidating {dataset_name}..."
    )


    check_required_columns(
        dataset_name,
        df
    )

    check_missing_values(
        dataset_name,
        df
    )

    check_duplicate_primary_key(
        dataset_name,
        df
    )

    check_whitespace(
        dataset_name,
        df
    )

    check_case_inconsistency(
        dataset_name,
        df
    )

    check_allowed_values(
        dataset_name,
        df
    )

    check_phone_numbers(
        dataset_name,
        df
    )

    check_duplicate_phones(
        dataset_name,
        df
    )

    check_numeric_columns(
        dataset_name,
        df
    )

    check_negative_values(
        dataset_name,
        df
    )

    check_date_columns(
        dataset_name,
        df
    )


check_refunds(
    datasets["payments"]
)


check_membership_dates(
    datasets["memberships"]
)


check_attendance_duration(
    datasets["attendance"]
)


check_cross_table_relationships(
    datasets["members"],
    datasets["memberships"],
    datasets["attendance"],
    datasets["payments"],
    datasets["leads"],
    datasets["followups"]
)


results_df = pd.DataFrame(
    results
)


report_file = (
    REPORT_DIR
    / "data_quality_report.csv"
)


results_df.to_csv(
    report_file,
    index=False
)


print("\nData Quality Report")

print(
    results_df[
        [
            "dataset",
            "check",
            "issue_count",
            "severity"
        ]
    ].to_string(index=False)
)

print("\nSummary")


critical_count = int(
    (
        results_df["severity"]
        == "CRITICAL"
    ).sum()
)


warning_count = int(
    (
        results_df["severity"]
        == "WARNING"
    ).sum()
)


pass_count = int(
    (
        results_df["severity"]
        == "PASS"
    ).sum()
)


info_count = int(
    (
        results_df["severity"]
        == "INFO"
    ).sum()
)


print(
    f"Critical issues: {critical_count}"
)

print(
    f"Warnings: {warning_count}"
)

print(
    f"Passed checks: {pass_count}"
)

print(
    f"Informational checks: {info_count}"
)


print("\nSaved report to:")

print(
    report_file
)


if critical_count > 0:

    print(
        "\nDATA QUALITY STATUS: CRITICAL ISSUES FOUND"
    )

elif warning_count > 0:

    print(
        "\nDATA QUALITY STATUS: ISSUES DETECTED"
    )

else:

    print(
        "\nDATA QUALITY STATUS: CLEAN"
    )