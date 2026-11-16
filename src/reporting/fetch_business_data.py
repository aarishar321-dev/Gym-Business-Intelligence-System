
from pathlib import Path
from datetime import datetime
import shutil
import os

import pandas as pd

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv

from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo


# 1. Set up project paths and load environment variables

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


# 2. Read database credentials

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fitcore_gym")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# 3. Validate database password

if not DB_PASSWORD:
    raise ValueError(
        "DB_PASSWORD is missing from the .env file"
    )


# 4. Create the PostgreSQL connection

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# 5. Fetch inactive members

inactive_query = text("""
    SELECT *
    FROM vw_inactive_active_members
    ORDER BY days_inactive DESC;
""")


# 6. Fetch memberships expiring within 7 days

expiring_query = text("""
    SELECT *
    FROM vw_expiring_members
    ORDER BY end_date;
""")


try:
    inactive_df = pd.read_sql(
        inactive_query,
        engine
    )

    expiring_df = pd.read_sql(
        expiring_query,
        engine
    )

finally:
    engine.dispose()


# 7. Display the business report in the terminal

report_date = datetime.now().date()

iso_year, iso_week, _ = report_date.isocalendar()

week_label = f"{iso_year}-W{iso_week:02d}"

print("\nFITCORE GYM BUSINESS REPORT")
print("=" * 45)

print(f"Report date: {report_date}")
print(f"Report week: {week_label}")

print(
    f"Inactive members (14+ days): "
    f"{len(inactive_df)}"
)

print(
    f"Memberships expiring within 7 days: "
    f"{len(expiring_df)}"
)


print("\nTOP 5 INACTIVE MEMBERS")

if not inactive_df.empty:
    print(
        inactive_df.head(5).to_string(
            index=False
        )
    )
else:
    print("No inactive members found.")


print("\nTOP 5 EXPIRING MEMBERSHIPS")

if not expiring_df.empty:
    print(
        expiring_df.head(5).to_string(
            index=False
        )
    )
else:
    print("No memberships expiring within 7 days.")


print("\nBusiness data fetched successfully.")


# 8. Create the executive summary

summary_df = pd.DataFrame({
    "Metric": [
        "Report Date",
        "Report Week",
        "Inactive Members (14+ Days)",
        "Memberships Expiring Within 7 Days"
    ],

    "Value": [
        report_date,
        week_label,
        len(inactive_df),
        len(expiring_df)
    ]
})


# 9. Create the reports and archive directories

REPORTS_DIR = PROJECT_ROOT / "reports"

ARCHIVE_DIR = REPORTS_DIR / "archive"

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

ARCHIVE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# 10. Define the latest Excel report path

excel_path = (
    REPORTS_DIR
    / "FitCore_Weekly_Business_Report.xlsx"
)


# 11. Export the data into three Excel sheets

with pd.ExcelWriter(
    excel_path,
    engine="openpyxl"
) as writer:

    summary_df.to_excel(
        writer,
        sheet_name="Executive Summary",
        index=False
    )

    inactive_df.to_excel(
        writer,
        sheet_name="Inactive Members",
        index=False
    )

    expiring_df.to_excel(
        writer,
        sheet_name="Expiring Memberships",
        index=False
    )


# 12. Load the exported workbook

workbook = load_workbook(excel_path)


# 13. Define the report styling

header_fill = PatternFill(
    fill_type="solid",
    fgColor="17365D"
)

header_font = Font(
    name="Arial",
    bold=True,
    color="FFFFFF",
    size=11
)

body_font = Font(
    name="Arial",
    size=10,
    color="222222"
)

thin_border = Border(
    bottom=Side(
        style="thin",
        color="D9E2F3"
    )
)


# 14. Format all worksheets

for worksheet in workbook.worksheets:

    for row in worksheet.iter_rows():
        for cell in row:
            cell.font = body_font
            cell.alignment = Alignment(
                vertical="center"
            )

    for cell in worksheet[1]:

        cell.font = header_font

        cell.fill = header_fill

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
        )

    worksheet.row_dimensions[1].height = 30

    worksheet.freeze_panes = "A2"

    if worksheet.max_column > 0:
        worksheet.auto_filter.ref = (
            worksheet.dimensions
        )

    for column_cells in worksheet.columns:

        max_length = 0

        column_letter = get_column_letter(
            column_cells[0].column
        )

        for cell in column_cells:

            if cell.value is not None:

                max_length = max(
                    max_length,
                    len(str(cell.value))
                )

        worksheet.column_dimensions[
            column_letter
        ].width = min(
            max_length + 4,
            35
        )

    for row in worksheet.iter_rows(
        min_row=2
    ):
        for cell in row:
            cell.border = thin_border


# 15. Format the executive summary

summary_sheet = workbook[
    "Executive Summary"
]

summary_sheet.column_dimensions[
    "A"
].width = 42

summary_sheet.column_dimensions[
    "B"
].width = 28

for row in range(
    2,
    summary_sheet.max_row + 1
):

    summary_sheet.cell(
        row=row,
        column=2
    ).font = Font(
        name="Arial",
        bold=True,
        size=11,
        color="17365D"
    )

    summary_sheet.cell(
        row=row,
        column=2
    ).alignment = Alignment(
        horizontal="center",
        vertical="center"
    )


# Format the report date

summary_sheet["B2"].number_format = (
    "yyyy-mm-dd"
)


# 16. Format date columns in detail sheets

for sheet_name in [
    "Inactive Members",
    "Expiring Memberships"
]:

    worksheet = workbook[sheet_name]

    headers = {
        str(cell.value): cell.column
        for cell in worksheet[1]
        if cell.value is not None
    }

    for date_column in [
        "last_visit",
        "last_visit_date",
        "end_date"
    ]:

        if date_column in headers:

            column_number = headers[
                date_column
            ]

            for row in range(
                2,
                worksheet.max_row + 1
            ):

                worksheet.cell(
                    row=row,
                    column=column_number
                ).number_format = "yyyy-mm-dd"


# 17. Add Excel tables to detail sheets

for sheet_name, table_name in [
    (
        "Inactive Members",
        "InactiveMembersTable"
    ),
    (
        "Expiring Memberships",
        "ExpiringMembershipsTable"
    )
]:

    worksheet = workbook[sheet_name]

    if worksheet.max_row >= 2:

        table = Table(
            displayName=table_name,
            ref=worksheet.dimensions
        )

        table_style = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False
        )

        table.tableStyleInfo = table_style

        worksheet.add_table(table)


# 18. Save the formatted latest workbook

workbook.save(excel_path)


# 19. Create the weekly archive copy

archive_filename = (
    f"FitCore_Weekly_Business_Report_{week_label}.xlsx"
)

archive_path = ARCHIVE_DIR / archive_filename

shutil.copy2(
    excel_path,
    archive_path
)


# 20. Confirm successful report generation

print(
    f"\nLatest Excel report saved to: {excel_path}"
)

print(
    f"Weekly archive saved to: {archive_path}"
)

print(
    "Excel formatting completed successfully."
)

print(
    "\nFITCORE WEEKLY BUSINESS REPORT "
    "GENERATED SUCCESSFULLY."
)