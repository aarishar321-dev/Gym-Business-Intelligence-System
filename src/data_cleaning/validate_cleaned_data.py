
import pandas as pd
from pathlib import Path

# File paths
DATA_DIR = Path("data/processed")
REPORT_DIR = Path("data/processed")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Load cleaned datasets
print("Loading cleaned datasets...")

members = pd.read_csv(DATA_DIR / "members.csv")
memberships = pd.read_csv(DATA_DIR / "memberships.csv")
attendance = pd.read_csv(DATA_DIR / "attendance.csv")
payments = pd.read_csv(DATA_DIR / "payments.csv")
leads = pd.read_csv(DATA_DIR / "leads.csv")
followups = pd.read_csv(DATA_DIR / "followups.csv")

print("\nAll datasets loaded successfully.")

datasets = {
    "members": members,
    "memberships": memberships,
    "attendance": attendance,
    "payments": payments,
    "leads": leads,
    "followups": followups
}

# Store validation results
results = []


def add_result(check, issue_count, severity):
    results.append({
        "check": check,
        "issue_count": int(issue_count),
        "severity": severity
    })


# 1. Check duplicate primary keys
print("\nChecking primary keys...")

primary_keys = {
    "members": ("member_id", members),
    "memberships": ("membership_id", memberships),
    "attendance": ("attendance_id", attendance),
    "payments": ("payment_id", payments),
    "leads": ("lead_id", leads),
    "followups": ("followup_id", followups)
}

for table_name, (key, df) in primary_keys.items():
    duplicates = df[key].duplicated().sum()
    add_result(
        f"{table_name}: duplicate {key}",
        duplicates,
        "CRITICAL" if duplicates > 0 else "PASS"
    )


# 2. Check member foreign keys
print("Checking member relationships...")

valid_member_ids = set(members["member_id"])

member_fk_checks = {
    "memberships": memberships["member_id"],
    "attendance": attendance["member_id"],
    "payments": payments["member_id"],
    "leads_converted": leads["converted_member_id"]
}

for table_name, column in member_fk_checks.items():
    # Empty converted_member_id is allowed for unconverted leads
    values = column.dropna()
    values = values[values.astype(str).str.strip() != ""]

    invalid = (~values.isin(valid_member_ids)).sum()

    add_result(
        f"{table_name}: invalid member foreign keys",
        invalid,
        "CRITICAL" if invalid > 0 else "PASS"
    )


# 3. Check payment membership relationships
print("Checking payment-to-membership relationships...")

valid_membership_ids = set(memberships["membership_id"])

invalid_membership_ids = (
    ~payments["membership_id"].isin(valid_membership_ids)
).sum()

add_result(
    "payments: invalid membership foreign keys",
    invalid_membership_ids,
    "CRITICAL" if invalid_membership_ids > 0 else "PASS"
)

# A payment's member must match the membership's member
membership_owner = memberships.set_index(
    "membership_id"
)["member_id"]

payment_membership_owner = payments["membership_id"].map(
    membership_owner
)

mismatched_owners = (
    payments["member_id"] != payment_membership_owner
).sum()

add_result(
    "payments: member does not own referenced membership",
    mismatched_owners,
    "CRITICAL" if mismatched_owners > 0 else "PASS"
)


# 4. Check follow-up-to-lead relationships
print("Checking follow-up relationships...")

valid_lead_ids = set(leads["lead_id"])

invalid_followup_leads = (
    ~followups["lead_id"].isin(valid_lead_ids)
).sum()

add_result(
    "followups: invalid lead foreign keys",
    invalid_followup_leads,
    "CRITICAL" if invalid_followup_leads > 0 else "PASS"
)


# 5. Check membership date relationships
print("Checking membership dates...")

memberships["start_date"] = pd.to_datetime(
    memberships["start_date"], errors="coerce"
)

memberships["end_date"] = pd.to_datetime(
    memberships["end_date"], errors="coerce"
)

invalid_membership_dates = (
    memberships["start_date"].isna()
    | memberships["end_date"].isna()
    | (memberships["end_date"] < memberships["start_date"])
).sum()

add_result(
    "memberships: invalid date ranges",
    invalid_membership_dates,
    "CRITICAL" if invalid_membership_dates > 0 else "PASS"
)


# 6. Check payment amounts and refunds
print("Checking payment amounts...")

payments["amount"] = pd.to_numeric(
    payments["amount"], errors="coerce"
)

payments["refund_amount"] = pd.to_numeric(
    payments["refund_amount"], errors="coerce"
)

invalid_payment_amounts = (
    payments["amount"].isna()
    | payments["refund_amount"].isna()
    | (payments["amount"] < 0)
    | (payments["refund_amount"] < 0)
    | (payments["refund_amount"] > payments["amount"])
).sum()

add_result(
    "payments: invalid amounts or refunds",
    invalid_payment_amounts,
    "CRITICAL" if invalid_payment_amounts > 0 else "PASS"
)


# 7. Check attendance dates and durations
print("Checking attendance records...")

attendance["check_in_date"] = pd.to_datetime(
    attendance["check_in_date"], errors="coerce"
)

attendance["session_duration"] = pd.to_numeric(
    attendance["session_duration"], errors="coerce"
)

invalid_attendance = (
    attendance["check_in_date"].isna()
    | attendance["session_duration"].isna()
    | (attendance["session_duration"] <= 0)
).sum()

add_result(
    "attendance: invalid dates or durations",
    invalid_attendance,
    "CRITICAL" if invalid_attendance > 0 else "PASS"
)


# 8. Check converted leads
print("Checking converted leads...")

converted_leads = leads[
    leads["status"].astype(str).str.upper() == "CONVERTED"
]

missing_converted_member = (
    converted_leads["converted_member_id"].isna()
    | (
        converted_leads["converted_member_id"]
        .astype("string")
        .str.strip()
        .eq("")
    )
).sum()

add_result(
    "leads: converted leads without member IDs",
    missing_converted_member,
    "WARNING" if missing_converted_member > 0 else "PASS"
)


# 9. Check for orphaned members
print("Checking member activity...")

members_with_memberships = set(memberships["member_id"])

members_without_memberships = (
    ~members["member_id"].isin(members_with_memberships)
).sum()

add_result(
    "members: members without memberships",
    members_without_memberships,
    "INFO"
)


# 10. Display and save validation report
report = pd.DataFrame(results)

print("\n" + "=" * 60)
print("CROSS-TABLE VALIDATION REPORT")
print("=" * 60)

print(report.to_string(index=False))

critical_count = (report["severity"] == "CRITICAL").sum()
warning_count = (report["severity"] == "WARNING").sum()
passed_count = (report["severity"] == "PASS").sum()
info_count = (report["severity"] == "INFO").sum()

print("\nSummary")
print(f"Critical issues: {critical_count}")
print(f"Warnings: {warning_count}")
print(f"Passed checks: {passed_count}")
print(f"Informational checks: {info_count}")

report_path = REPORT_DIR / "cross_table_validation_report.csv"
report.to_csv(report_path, index=False)

print(f"\nReport saved to: {report_path}")

if critical_count > 0:
    print("\nSTATUS: CRITICAL ISSUES FOUND")
else:
    print("\nSTATUS: CROSS-TABLE VALIDATION PASSED")