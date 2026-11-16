
from pathlib import Path
from datetime import datetime
import os
import shutil

import pandas as pd

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether
)


# 1. Set up project paths and environment variables

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

REPORTS_DIR = PROJECT_ROOT / "reports"

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)

# Create the weekly archive directory

ARCHIVE_DIR = REPORTS_DIR / "archive"

ARCHIVE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# 2. Read database credentials

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fitcore_gym")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# 3. Validate the database password

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
    database=DB_NAME
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# 5. Define the SQL queries

inactive_query = text("""
    SELECT *
    FROM vw_inactive_active_members
    ORDER BY days_inactive DESC;
""")

expiring_query = text("""
    SELECT *
    FROM vw_expiring_members
    ORDER BY end_date;
""")


# 6. Fetch data from PostgreSQL

try:

    with engine.connect() as connection:

        inactive_df = pd.read_sql(
            inactive_query,
            connection
        )

        expiring_df = pd.read_sql(
            expiring_query,
            connection
        )

finally:

    engine.dispose()


# 7. Define report information

report_date = datetime.now().date()

# ISO year and week number
# Example: 2026-W40

iso_year, iso_week, _ = report_date.isocalendar()

week_label = f"{iso_year}-W{iso_week:02d}"

inactive_count = len(inactive_df)

expiring_count = len(expiring_df)


# 8. Define the PDF output paths

# Latest PDF (overwritten every time the script runs)

pdf_path = (
    REPORTS_DIR
    / "FitCore_Weekly_Business_Report.pdf"
)

# Archived PDF for the current ISO week

archive_filename = (
    f"FitCore_Weekly_Business_Report_{week_label}.pdf"
)

archive_path = (
    ARCHIVE_DIR
    / archive_filename
)


# 9. Create the PDF document

document = SimpleDocTemplate(
    str(pdf_path),
    pagesize=landscape(A4),
    rightMargin=15 * mm,
    leftMargin=15 * mm,
    topMargin=18 * mm,
    bottomMargin=18 * mm,
    title="FitCore Weekly Business Report",
    author="FitCore Gym"
)


# 10. Define the report colors

NAVY = colors.HexColor("#17365D")
BLUE = colors.HexColor("#4472C4")
LIGHT_BLUE = colors.HexColor("#D9EAF7")
LIGHT_GREY = colors.HexColor("#F2F4F7")
DARK_GREY = colors.HexColor("#444444")
WHITE = colors.white


# 11. Define the report styles

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "FitCoreTitle",
    parent=styles["Title"],
    fontName="Helvetica-Bold",
    fontSize=22,
    leading=27,
    textColor=NAVY,
    alignment=TA_CENTER,
    spaceAfter=6
)

subtitle_style = ParagraphStyle(
    "FitCoreSubtitle",
    parent=styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    textColor=DARK_GREY,
    alignment=TA_CENTER,
    spaceAfter=12
)

section_style = ParagraphStyle(
    "FitCoreSection",
    parent=styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=18,
    textColor=NAVY,
    spaceBefore=12,
    spaceAfter=8
)

body_style = ParagraphStyle(
    "FitCoreBody",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=9,
    leading=13,
    textColor=DARK_GREY,
    spaceAfter=5
)

small_style = ParagraphStyle(
    "FitCoreSmall",
    parent=styles["BodyText"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=DARK_GREY
)


# 12. Create a helper to format table values

def format_value(value):

    if pd.isna(value):
        return "-"

    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")

    return str(value)


# 13. Create a helper to build PDF tables

def create_pdf_table(
    dataframe,
    max_rows=None
):

    if dataframe.empty:

        empty_table = Table(
            [["No records found."]],
            colWidths=[250 * mm]
        )

        empty_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_GREY
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, -1),
                    DARK_GREY
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    "Helvetica"
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    8
                )
            ])
        )

        return empty_table

    display_df = dataframe.copy()

    if max_rows is not None:
        display_df = display_df.head(max_rows)

    headers = [
        str(column).replace("_", " ").title()
        for column in display_df.columns
    ]

    rows = [headers]

    for _, row in display_df.iterrows():

        formatted_row = [
            format_value(value)
            for value in row
        ]

        rows.append(formatted_row)

    number_of_columns = len(headers)

    available_width = (
        landscape(A4)[0]
        - document.leftMargin
        - document.rightMargin
    )

    column_width = (
        available_width
        / number_of_columns
    )

    table = Table(
        rows,
        repeatRows=1,
        colWidths=[
            column_width
        ] * number_of_columns,
        hAlign="LEFT"
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                NAVY
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                WHITE
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, 0),
                8
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, -1),
                WHITE
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, -1),
                "Helvetica"
            ),
            (
                "FONTSIZE",
                (0, 1),
                (-1, -1),
                7
            ),
            (
                "TEXTCOLOR",
                (0, 1),
                (-1, -1),
                DARK_GREY
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.3,
                colors.HexColor("#D9E2F3")
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    WHITE,
                    LIGHT_GREY
                ]
            )
        ])
    )

    return table


# 14. Add a footer with page numbers

def add_page_footer(
    canvas,
    document
):

    canvas.saveState()

    page_width, page_height = landscape(A4)

    canvas.setStrokeColor(
        colors.HexColor("#D9E2F3")
    )

    canvas.line(
        15 * mm,
        12 * mm,
        page_width - 15 * mm,
        12 * mm
    )

    canvas.setFont(
        "Helvetica",
        8
    )

    canvas.setFillColor(DARK_GREY)

    canvas.drawString(
        15 * mm,
        7 * mm,
        "FitCore Gym | Weekly Business Report"
    )

    canvas.drawRightString(
        page_width - 15 * mm,
        7 * mm,
        f"Page {document.page}"
    )

    canvas.restoreState()


# 15. Build the report content

story = []


# Report heading

story.append(
    Paragraph(
        "FITCORE GYM",
        title_style
    )
)

story.append(
    Paragraph(
        "WEEKLY BUSINESS REPORT",
        subtitle_style
    )
)

story.append(
    Paragraph(
        f"<b>Report Date:</b> "
        f"{report_date.strftime('%d %B %Y')}",
        subtitle_style
    )
)

story.append(
    Spacer(
        1,
        8
    )
)


# Executive summary

story.append(
    Paragraph(
        "1. Executive Summary",
        section_style
    )
)

summary_data = [
    ["Business Metric", "Current Value"],
    [
        "Inactive Members (14+ Days)",
        str(inactive_count)
    ],
    [
        "Memberships Expiring Within 7 Days",
        str(expiring_count)
    ]
]

summary_table = Table(
    summary_data,
    colWidths=[
        110 * mm,
        55 * mm
    ],
    hAlign="LEFT"
)

summary_table.setStyle(
    TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            NAVY
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            WHITE
        ),
        (
            "FONTNAME",
            (0, 0),
            (-1, 0),
            "Helvetica-Bold"
        ),
        (
            "FONTNAME",
            (0, 1),
            (-1, -1),
            "Helvetica"
        ),
        (
            "FONTSIZE",
            (0, 0),
            (-1, -1),
            10
        ),
        (
            "BACKGROUND",
            (0, 1),
            (-1, -1),
            LIGHT_BLUE
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.5,
            WHITE
        ),
        (
            "ALIGN",
            (1, 0),
            (1, -1),
            "CENTER"
        ),
        (
            "PADDING",
            (0, 0),
            (-1, -1),
            8
        )
    ])
)

story.append(summary_table)

story.append(
    Spacer(
        1,
        10
    )
)


# Inactive members section

story.append(
    Paragraph(
        "2. Inactive Members",
        section_style
    )
)

story.append(
    Paragraph(
        "The following members have not visited the gym "
        "for at least 14 days. The table is ordered by "
        "the number of inactive days, highest first.",
        body_style
    )
)

story.append(
    create_pdf_table(
        inactive_df
    )
)

story.append(
    Spacer(
        1,
        10
    )
)


# Expiring memberships section

story.append(
    Paragraph(
        "3. Memberships Expiring Within 7 Days",
        section_style
    )
)

story.append(
    Paragraph(
        "These members have memberships expiring within "
        "the next seven days, including memberships "
        "expiring today. Follow-up may help support "
        "timely renewals.",
        body_style
    )
)

story.append(
    create_pdf_table(
        expiring_df
    )
)


# Report generation note

story.append(
    Spacer(
        1,
        12
    )
)

story.append(
    Paragraph(
        "Report generated automatically from the "
        "FitCore Gym PostgreSQL database.",
        small_style
    )
)


# 16. Generate the latest PDF

document.build(
    story,
    onFirstPage=add_page_footer,
    onLaterPages=add_page_footer
)


# 17. Archive the PDF for the current week

# Copies the latest PDF into the archive folder.
# If this week's archive already exists, it is overwritten.

shutil.copy2(
    pdf_path,
    archive_path
)


# 18. Confirm successful generation

print("\nFITCORE WEEKLY PDF REPORT")

print("=" * 40)

print(
    f"Report date: {report_date}"
)

print(
    f"Report week: {week_label}"
)

print(
    f"Inactive members: {inactive_count}"
)

print(
    f"Memberships expiring within 7 days: "
    f"{expiring_count}"
)

print(
    f"\nLatest PDF saved to: {pdf_path}"
)

print(
    f"Weekly archive saved to: {archive_path}"
)

print(
    "\nFITCORE WEEKLY PDF REPORT "
    "GENERATED SUCCESSFULLY."
)