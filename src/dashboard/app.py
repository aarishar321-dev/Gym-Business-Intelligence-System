from pathlib import Path
from io import BytesIO
from datetime import date, timedelta
import os
import re

import pandas as pd
import streamlit as st
import plotly.express as px

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv


# ============================================================
# 1. CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FitCore Gym Dashboard",
    page_icon="",
    layout="wide"
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

REPORTS_DIR = PROJECT_ROOT / "reports"
ARCHIVE_DIR = REPORTS_DIR / "archive"

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fitcore_gym")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_PASSWORD:
    st.error("DB_PASSWORD is missing from your .env file.")
    st.stop()

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)


@st.cache_resource
def get_engine():
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )


engine = get_engine()


def fetch_data(query, params=None):
    """Execute a SQL query and return a DataFrame."""

    with engine.connect() as connection:
        return pd.read_sql(
            text(query),
            connection,
            params=params or {}
        )


# ============================================================
# 2. DATABASE DATE COVERAGE
# ============================================================

@st.cache_data(ttl=300)
def load_date_coverage():

    return fetch_data("""
        SELECT
            MIN(activity_date) AS first_date,
            MAX(activity_date) AS last_date

        FROM (
            SELECT payment_date AS activity_date
            FROM payments

            UNION ALL

            SELECT enquiry_date
            FROM leads

            UNION ALL

            SELECT join_date
            FROM members

            UNION ALL

            SELECT check_in_date
            FROM attendance

            UNION ALL

            SELECT start_date
            FROM memberships

        ) AS all_dates

        WHERE activity_date IS NOT NULL
    """)


# ============================================================
# 3. HISTORICAL BUSINESS QUERIES
# ============================================================

@st.cache_data(ttl=300)
def load_period_data(start_date, end_date):

    params = {
        "start_date": start_date,
        "end_date": end_date,
        "period_end": end_date
    }

    # --------------------------------------------------------
    # REVENUE
    # --------------------------------------------------------

    revenue = fetch_data("""
        SELECT
            payment_date,

            SUM(
                amount - COALESCE(refund_amount, 0)
            ) AS net_revenue,

            COUNT(*) AS payment_count

        FROM payments

        WHERE payment_status = 'SUCCESS'
          AND payment_date BETWEEN
              :start_date AND :end_date

        GROUP BY payment_date

        ORDER BY payment_date
    """, params)

    if not revenue.empty:
        revenue["payment_date"] = pd.to_datetime(
            revenue["payment_date"]
        )

    # --------------------------------------------------------
    # LEAD ENQUIRY COHORT AND CONVERSION
    # --------------------------------------------------------

    leads = fetch_data("""
        SELECT
            enquiry_date,

            COUNT(*) AS total_leads,

            COUNT(*) FILTER (
                WHERE status = 'CONVERTED'
            ) AS converted_leads,

            COUNT(*) FILTER (
                WHERE status = 'QUALIFIED'
            ) AS qualified_leads

        FROM leads

        WHERE enquiry_date BETWEEN
              :start_date AND :end_date

        GROUP BY enquiry_date

        ORDER BY enquiry_date
    """, params)

    if not leads.empty:
        leads["enquiry_date"] = pd.to_datetime(
            leads["enquiry_date"]
        )

    # --------------------------------------------------------
    # LEAD PIPELINE
    # --------------------------------------------------------

    lead_pipeline = fetch_data("""
        SELECT
            status,
            COUNT(*) AS total_leads

        FROM leads

        WHERE enquiry_date BETWEEN
              :start_date AND :end_date

        GROUP BY status

        ORDER BY total_leads DESC
    """, params)

    # --------------------------------------------------------
    # MEMBERSHIP GROWTH
    # --------------------------------------------------------

    membership_growth = fetch_data("""
        SELECT
            join_date,
            COUNT(*) AS new_members

        FROM members

        WHERE join_date BETWEEN
              :start_date AND :end_date

        GROUP BY join_date

        ORDER BY join_date
    """, params)

    if not membership_growth.empty:
        membership_growth["join_date"] = pd.to_datetime(
            membership_growth["join_date"]
        )

    # --------------------------------------------------------
    # MEMBERSHIP STARTS AND RENEWALS
    # --------------------------------------------------------

    membership_activity = fetch_data("""
        SELECT
            ms.membership_id,
            ms.member_id,
            ms.plan,
            ms.start_date,
            ms.end_date,
            ms.price,

            CASE
                WHEN EXISTS (
                    SELECT 1

                    FROM memberships previous

                    WHERE previous.member_id = ms.member_id
                      AND previous.start_date < ms.start_date
                )

                THEN 1
                ELSE 0

            END AS is_renewal

        FROM memberships ms

        WHERE ms.start_date BETWEEN
              :start_date AND :end_date

        ORDER BY ms.start_date
    """, params)

    # --------------------------------------------------------
    # ACTIVE MEMBERS AT PERIOD END
    #
    # FIXED:
    # Only ACTIVE memberships are counted.
    #
    # Previously, status <> 'ACTIVE' counted CANCELLED
    # and EXPIRED records as active.
    # --------------------------------------------------------

    active_at_period_end = fetch_data("""
        SELECT
            COUNT(DISTINCT member_id) AS active_members
        FROM memberships
        WHERE start_date <= :period_end
        AND end_date >= :period_end
        AND status = 'ACTIVE'
    """, params)

    # --------------------------------------------------------
    # INACTIVE MEMBERS AT PERIOD END
    #
    # FIXED:
    # Only ACTIVE memberships are included.
    #
    # A member is inactive when their last attendance
    # was more than 14 days before the selected end date.
    # --------------------------------------------------------

    inactive_members = fetch_data("""
        WITH active_members AS (

            SELECT DISTINCT member_id

            FROM memberships

            WHERE start_date <= :period_end
              AND end_date >= :period_end
              AND status = 'ACTIVE'
        ),

        last_attendance AS (

            SELECT
                member_id,
                MAX(check_in_date) AS last_visit

            FROM attendance

            WHERE check_in_date <= :period_end

            GROUP BY member_id
        )

        SELECT
            m.member_id,
            m.name,
            la.last_visit,

            CASE
                WHEN la.last_visit IS NULL
                    THEN NULL

                ELSE
                    (:period_end - la.last_visit)

            END AS days_inactive

        FROM active_members am

        JOIN members m
          ON m.member_id = am.member_id

        LEFT JOIN last_attendance la
          ON la.member_id = am.member_id

        WHERE la.last_visit IS NULL

           OR la.last_visit <
              (:period_end - INTERVAL '14 days')

        ORDER BY la.last_visit NULLS FIRST
    """, params)

    # --------------------------------------------------------
    # UPCOMING RENEWALS AS OF PERIOD END
    # --------------------------------------------------------

    expiring_members = fetch_data("""
        SELECT
            m.member_id,
            m.name,
            ms.plan,
            ms.end_date

        FROM memberships ms

        JOIN members m
          ON m.member_id = ms.member_id

        WHERE ms.status = 'ACTIVE'

          AND ms.start_date <= :period_end

          AND ms.end_date BETWEEN
              :period_end
              AND (:period_end + INTERVAL '7 days')

        ORDER BY ms.end_date
    """, params)

    return {
        "revenue": revenue,
        "leads": leads,
        "lead_pipeline": lead_pipeline,
        "membership_growth": membership_growth,
        "membership_activity": membership_activity,
        "active_at_period_end": active_at_period_end,
        "inactive_members": inactive_members,
        "expiring_members": expiring_members
    }


# ============================================================
# 4. PERIOD KPI CALCULATIONS
# ============================================================

def calculate_kpis(data):

    revenue_df = data["revenue"]
    leads_df = data["leads"]
    growth_df = data["membership_growth"]
    membership_df = data["membership_activity"]

    net_revenue = (
        revenue_df["net_revenue"].sum()
        if not revenue_df.empty
        else 0
    )

    total_leads = (
        leads_df["total_leads"].sum()
        if not leads_df.empty
        else 0
    )

    converted_leads = (
        leads_df["converted_leads"].sum()
        if not leads_df.empty
        else 0
    )

    conversion_rate = (
        converted_leads / total_leads * 100
        if total_leads
        else 0
    )

    new_members = (
        growth_df["new_members"].sum()
        if not growth_df.empty
        else 0
    )

    renewals = (
        membership_df["is_renewal"].sum()
        if not membership_df.empty
        else 0
    )

    membership_starts = len(membership_df)

    # Corrected active-member count.
    active_members = int(
        data["active_at_period_end"].iloc[0][
            "active_members"
        ]
    )

    inactive_count = len(
        data["inactive_members"]
    )

    expiring_count = len(
        data["expiring_members"]
    )

    return {
        "revenue": float(net_revenue),
        "total_leads": int(total_leads),
        "converted_leads": int(converted_leads),
        "conversion_rate": float(conversion_rate),
        "new_members": int(new_members),
        "membership_starts": int(membership_starts),
        "renewals": int(renewals),
        "active_members": active_members,
        "inactive_members": inactive_count,
        "expiring_members": expiring_count
    }


# ============================================================
# 5. EXCEL EXPORT
# ============================================================

def create_excel_report(
    data,
    current_kpis,
    previous_kpis,
    start_date,
    end_date,
    previous_start,
    previous_end
):

    output = BytesIO()

    summary = pd.DataFrame([
        {
            "Metric": metric,
            "Selected Period": value,
            "Previous Period": previous_kpis.get(
                metric, 0
            ),
            "Change": (
                value - previous_kpis.get(metric, 0)
            )
        }

        for metric, value in current_kpis.items()
    ])

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        summary.to_excel(
            writer,
            sheet_name="Executive Summary",
            index=False
        )

        data["revenue"].to_excel(
            writer,
            sheet_name="Revenue",
            index=False
        )

        data["leads"].to_excel(
            writer,
            sheet_name="Lead Analytics",
            index=False
        )

        data["lead_pipeline"].to_excel(
            writer,
            sheet_name="Lead Pipeline",
            index=False
        )

        data["membership_growth"].to_excel(
            writer,
            sheet_name="Membership Growth",
            index=False
        )

        data["membership_activity"].to_excel(
            writer,
            sheet_name="Membership Activity",
            index=False
        )

        data["inactive_members"].to_excel(
            writer,
            sheet_name="Inactive Members",
            index=False
        )

        data["expiring_members"].to_excel(
            writer,
            sheet_name="Upcoming Renewals",
            index=False
        )

        for worksheet in writer.book.worksheets:

            worksheet.freeze_panes = "A2"

            worksheet.auto_filter.ref = (
                worksheet.dimensions
            )

            for column_cells in worksheet.columns:

                max_length = max(
                    len(str(cell.value or ""))
                    for cell in column_cells
                )

                worksheet.column_dimensions[
                    column_cells[0].column_letter
                ].width = min(
                    max_length + 3,
                    35
                )

    output.seek(0)

    return output.getvalue()


# ============================================================
# 6. PDF EXPORT WITH CHARTS
# ============================================================

def create_pdf_report(
    data,
    current_kpis,
    previous_kpis,
    start_date,
    end_date,
    previous_start,
    previous_end
):

    try:
        import matplotlib.pyplot as plt

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch

        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            Image
        )

    except ImportError as error:

        raise RuntimeError(
            "PDF dependencies are missing. "
            "Install reportlab and matplotlib."
        ) from error

    output = BytesIO()

    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "FitCore Gym - Historical Business Report",
            styles["Title"]
        )
    )

    story.append(
        Paragraph(
            f"Reporting period: {start_date} to {end_date}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"Comparison period: "
            f"{previous_start} to {previous_end}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 15))

    # Executive summary

    summary_data = [
        [
            "Metric",
            "Selected Period",
            "Previous Period",
            "Change"
        ]
    ]

    for metric, value in current_kpis.items():

        previous_value = previous_kpis.get(
            metric, 0
        )

        summary_data.append([
            metric.replace("_", " ").title(),

            f"{value:,.2f}"
            if isinstance(value, float)
            else f"{value:,}",

            f"{previous_value:,.2f}"
            if isinstance(previous_value, float)
            else f"{previous_value:,}",

            f"{value - previous_value:,.2f}"
            if isinstance(value, float)
            else f"{value - previous_value:,}"
        ])

    summary_table = Table(
        summary_data,
        repeatRows=1
    )

    summary_table.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#1F4E78")
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.4,
            colors.grey
        ),
        (
            "FONTSIZE",
            (0, 0),
            (-1, -1),
            8
        ),
        (
            "PADDING",
            (0, 0),
            (-1, -1),
            6
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "MIDDLE"
        )
    ]))

    story.append(summary_table)

    story.append(Spacer(1, 20))

    # Revenue chart

    revenue_df = data["revenue"]

    if not revenue_df.empty:

        chart_buffer = BytesIO()

        plt.figure(figsize=(8, 3.5))

        plt.bar(
            revenue_df["payment_date"].astype(str),
            revenue_df["net_revenue"]
        )

        plt.title("Net Revenue by Payment Date")
        plt.xlabel("Payment Date")
        plt.ylabel("Net Revenue (INR)")

        plt.xticks(
            rotation=45,
            ha="right"
        )

        plt.tight_layout()

        plt.savefig(
            chart_buffer,
            format="png",
            dpi=150
        )

        plt.close()

        chart_buffer.seek(0)

        story.append(
            Paragraph(
                "Revenue Analytics",
                styles["Heading2"]
            )
        )

        story.append(
            Image(
                chart_buffer,
                width=7.5 * inch,
                height=3.3 * inch
            )
        )

        story.append(Spacer(1, 15))

    # Lead conversion chart

    leads_df = data["leads"]

    if not leads_df.empty:

        chart_buffer = BytesIO()

        plt.figure(figsize=(8, 3.5))

        plt.plot(
            leads_df["enquiry_date"],
            leads_df["total_leads"],
            label="Total Enquiries",
            marker="o"
        )

        plt.plot(
            leads_df["enquiry_date"],
            leads_df["converted_leads"],
            label="Converted Leads (Enquiry Cohort)",
            marker="o"
        )

        plt.title(
            "Lead Enquiries and Conversion Cohort"
        )

        plt.xlabel("Enquiry Date")
        plt.ylabel("Lead Count")

        plt.legend()

        plt.xticks(
            rotation=45,
            ha="right"
        )

        plt.tight_layout()

        plt.savefig(
            chart_buffer,
            format="png",
            dpi=150
        )

        plt.close()

        chart_buffer.seek(0)

        story.append(
            Paragraph(
                "Lead Analytics",
                styles["Heading2"]
            )
        )

        story.append(
            Image(
                chart_buffer,
                width=7.5 * inch,
                height=3.3 * inch
            )
        )

        story.append(Spacer(1, 15))

    # Membership growth chart

    growth_df = data["membership_growth"]

    if not growth_df.empty:

        chart_buffer = BytesIO()

        plt.figure(figsize=(8, 3.5))

        plt.bar(
            growth_df["join_date"].astype(str),
            growth_df["new_members"]
        )

        plt.title("New Member Registrations")
        plt.xlabel("Join Date")
        plt.ylabel("New Members")

        plt.xticks(
            rotation=45,
            ha="right"
        )

        plt.tight_layout()

        plt.savefig(
            chart_buffer,
            format="png",
            dpi=150
        )

        plt.close()

        chart_buffer.seek(0)

        story.append(
            Paragraph(
                "Membership Growth",
                styles["Heading2"]
            )
        )

        story.append(
            Image(
                chart_buffer,
                width=7.5 * inch,
                height=3.3 * inch
            )
        )

        story.append(Spacer(1, 15))

    # Inactive member detail

    story.append(
        Paragraph(
            "Inactive Members",
            styles["Heading2"]
        )
    )

    inactive_df = data["inactive_members"]

    inactive_table_data = [
        [
            "Member ID",
            "Name",
            "Last Visit",
            "Days Inactive"
        ]
    ]

    for _, row in inactive_df.head(30).iterrows():

        inactive_table_data.append([
            str(row["member_id"]),
            str(row["name"]),

            str(row["last_visit"])
            if pd.notna(row["last_visit"])
            else "No attendance",

            str(row["days_inactive"])
            if pd.notna(row["days_inactive"])
            else "N/A"
        ])

    inactive_table = Table(
        inactive_table_data,
        repeatRows=1
    )

    inactive_table.setStyle(TableStyle([
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#1F4E78")
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.4,
            colors.grey
        ),
        (
            "FONTSIZE",
            (0, 0),
            (-1, -1),
            8
        ),
        (
            "PADDING",
            (0, 0),
            (-1, -1),
            5
        )
    ]))

    story.append(inactive_table)

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "Note: Lead conversion is grouped by enquiry "
            "date because the database does not currently "
            "store a conversion timestamp. Historical active "
            "and inactive member figures are reconstructed "
            "from membership date ranges and attendance "
            "records. Historical cancellation status cannot "
            "be fully reconstructed without a cancellation "
            "timestamp.",
            styles["Italic"]
        )
    )

    doc.build(story)

    output.seek(0)

    return output.getvalue()


# ============================================================
# 7. DASHBOARD HEADER
# ============================================================

st.title("FitCore Gym")

st.subheader(
    "Historical Business Intelligence Dashboard"
)

st.caption(
    "PostgreSQL-powered business analytics | "
    "Synthetic FitCore dataset"
)

if st.button("Refresh dashboard"):

    st.cache_data.clear()

    st.rerun()


# ============================================================
# 8. DATE / WEEK SELECTOR
# ============================================================

try:

    coverage_df = load_date_coverage()

    if (
        coverage_df.empty
        or pd.isna(coverage_df.iloc[0]["first_date"])
    ):

        st.error("No dated business records found.")

        st.stop()

    min_date = pd.to_datetime(
        coverage_df.iloc[0]["first_date"]
    ).date()

    max_date = min(
        pd.to_datetime(
            coverage_df.iloc[0]["last_date"]
        ).date(),
        date.today()
    )

except Exception as error:

    st.error(
        f"Could not determine data coverage: {error}"
    )

    st.stop()


st.markdown("### Select Reporting Period")

period_mode = st.radio(
    "Reporting period type",
    ["Reporting Week", "Custom Date Range"],
    horizontal=True
)

if period_mode == "Reporting Week":

    week_options = []

    current_week_start = (
        min_date
        - timedelta(days=min_date.weekday())
    )

    last_week_start = (
        max_date
        - timedelta(days=max_date.weekday())
    )

    while current_week_start <= last_week_start:

        week_end = (
            current_week_start + timedelta(days=6)
        )

        if (
            week_end >= min_date
            and current_week_start <= max_date
        ):

            iso_year, iso_week, _ = (
                current_week_start.isocalendar()
            )

            week_label = (
                f"{iso_year}-W{iso_week:02d} "
                f"({current_week_start} to {week_end})"
            )

            week_options.append((
                week_label,
                current_week_start,
                week_end
            ))

        current_week_start += timedelta(days=7)

    if not week_options:

        st.error("No reporting weeks available.")

        st.stop()

    selected_label = st.selectbox(
        "Select reporting week",
        options=[
            item[0]
            for item in reversed(week_options)
        ]
    )

    selected_week = next(
        item
        for item in week_options
        if item[0] == selected_label
    )

    start_date = max(
        selected_week[1],
        min_date
    )

    end_date = min(
        selected_week[2],
        max_date
    )

else:

    date_range = st.date_input(
        "Select custom date range",

        value=(
            max(
                min_date,
                max_date - timedelta(days=6)
            ),
            max_date
        ),

        min_value=min_date,
        max_value=max_date
    )

    if (
        not isinstance(date_range, (tuple, list))
        or len(date_range) != 2
    ):

        st.info(
            "Select both a start date and an end date."
        )

        st.stop()

    start_date, end_date = date_range

    if start_date > end_date:

        st.error(
            "Start date cannot be after end date."
        )

        st.stop()


# Previous period of equal duration

period_days = (
    end_date - start_date
).days + 1

previous_end = start_date - timedelta(days=1)

previous_start = previous_end - timedelta(
    days=period_days - 1
)

st.info(
    f"Selected period: {start_date} to {end_date} "
    f"({period_days} days)"
)


# ============================================================
# 9. LOAD CURRENT AND PREVIOUS PERIODS
# ============================================================

try:

    current_data = load_period_data(
        start_date,
        end_date
    )

    previous_data = load_period_data(
        previous_start,
        previous_end
    )

    current_kpis = calculate_kpis(
        current_data
    )

    previous_kpis = calculate_kpis(
        previous_data
    )

except Exception as error:

    st.error(
        f"Could not load historical business data: {error}"
    )

    st.exception(error)

    st.stop()


# ============================================================
# 10. HISTORICAL KPI CARDS
# ============================================================

st.markdown("### Business Performance")

st.caption(
    "Compared with the immediately preceding period "
    "of the same duration."
)


def display_metric(
    column,
    label,
    key,
    prefix="",
    suffix=""
):

    current = current_kpis[key]

    previous = previous_kpis[key]

    delta = current - previous

    column.metric(
        label,

        (
            f"{prefix}{current:,.1f}{suffix}"
            if isinstance(current, float)
            else f"{prefix}{current:,}{suffix}"
        ),

        delta=(
            f"{prefix}{delta:,.1f}{suffix}"
            if isinstance(delta, float)
            else f"{prefix}{delta:,}{suffix}"
        )
    )


kpi_col1, kpi_col2, kpi_col3, kpi_col4 = (
    st.columns(4)
)

display_metric(
    kpi_col1,
    "Net Revenue",
    "revenue",
    prefix="₹"
)

display_metric(
    kpi_col2,
    "Lead Conversion Rate*",
    "conversion_rate",
    suffix="%"
)

display_metric(
    kpi_col3,
    "New Members",
    "new_members"
)

display_metric(
    kpi_col4,
    "Renewals",
    "renewals"
)


kpi_col5, kpi_col6, kpi_col7, kpi_col8 = (
    st.columns(4)
)

display_metric(
    kpi_col5,
    "Total Enquiries",
    "total_leads"
)

display_metric(
    kpi_col6,
    "Converted Leads*",
    "converted_leads"
)

display_metric(
    kpi_col7,
    "Active Members at Period End",
    "active_members"
)

display_metric(
    kpi_col8,
    "Inactive Members (14+ Days)",
    "inactive_members"
)


st.caption(
    "*Lead conversion metrics are based on the "
    "enquiry-date cohort and current lead status, "
    "not the actual date of conversion."
)


# ============================================================
# 11. HISTORICAL CHARTS
# ============================================================

st.markdown(
    "### Historical Revenue & Lead Analytics"
)

chart_col1, chart_col2 = st.columns(2)

with chart_col1:

    st.markdown("#### Net Revenue")

    revenue_df = current_data["revenue"]

    if not revenue_df.empty:

        revenue_chart = px.bar(
            revenue_df,
            x="payment_date",
            y="net_revenue",

            labels={
                "payment_date": "Payment Date",
                "net_revenue": "Net Revenue (₹)"
            },

            title="Revenue for Selected Period"
        )

        st.plotly_chart(
            revenue_chart,
            use_container_width=True
        )

    else:

        st.info(
            "No successful payments in this period."
        )


with chart_col2:

    st.markdown("#### Lead Conversion Cohort")

    leads_df = current_data["leads"]

    if not leads_df.empty:

        lead_chart = px.line(
            leads_df,

            x="enquiry_date",

            y=[
                "total_leads",
                "converted_leads"
            ],

            markers=True,

            labels={
                "enquiry_date": "Enquiry Date",
                "value": "Lead Count",
                "variable": "Metric"
            },

            title="Enquiries and Converted Leads"
        )

        st.plotly_chart(
            lead_chart,
            use_container_width=True
        )

    else:

        st.info(
            "No lead enquiries in this period."
        )


st.markdown("### Membership Analytics")

membership_col1, membership_col2 = (
    st.columns(2)
)

with membership_col1:

    st.markdown("#### Membership Growth")

    growth_df = current_data[
        "membership_growth"
    ]

    if not growth_df.empty:

        growth_chart = px.bar(
            growth_df,

            x="join_date",
            y="new_members",

            labels={
                "join_date": "Join Date",
                "new_members": "New Members"
            },

            title="New Member Registrations"
        )

        st.plotly_chart(
            growth_chart,
            use_container_width=True
        )

    else:

        st.info(
            "No new members in this period."
        )


with membership_col2:

    st.markdown("#### Lead Pipeline")

    pipeline_df = current_data[
        "lead_pipeline"
    ]

    if not pipeline_df.empty:

        pipeline_chart = px.pie(
            pipeline_df,

            names="status",
            values="total_leads",

            hole=0.45,

            title=(
                "Lead Status for Selected "
                "Enquiry Cohort"
            )
        )

        st.plotly_chart(
            pipeline_chart,
            use_container_width=True
        )

    else:

        st.info(
            "No lead pipeline data available."
        )


# ============================================================
# 12. MEMBERSHIP ALERTS
# ============================================================

st.markdown(
    "### Historical Membership Alerts"
)

alert_col1, alert_col2 = st.columns(2)

with alert_col1:

    st.markdown("#### Inactive Members")

    st.metric(
        "Members Inactive for 14+ Days",
        len(current_data["inactive_members"])
    )

    st.dataframe(
        current_data["inactive_members"],
        use_container_width=True,
        hide_index=True
    )


with alert_col2:

    st.markdown("#### Upcoming Renewals")

    st.metric(
        "Memberships Expiring Within 7 Days",
        len(current_data["expiring_members"])
    )

    st.dataframe(
        current_data["expiring_members"],
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 13. PERIOD-SPECIFIC EXCEL AND PDF EXPORTS
# ============================================================

st.divider()

st.markdown("### Export Selected Period")

st.caption(
    "Generate reports using the selected dates, "
    "including period KPIs, previous-period "
    "comparisons, charts, and supporting business tables."
)

export_col1, export_col2 = st.columns(2)

period_filename = (
    f"FitCore_Report_{start_date}_to_{end_date}"
)


with export_col1:

    try:

        excel_bytes = create_excel_report(
            current_data,
            current_kpis,
            previous_kpis,
            start_date,
            end_date,
            previous_start,
            previous_end
        )

        st.download_button(
            label="Download Selected Period Excel",

            data=excel_bytes,

            file_name=f"{period_filename}.xlsx",

            mime=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),

            key="download_period_excel"
        )

    except Exception as error:

        st.error(
            f"Excel export failed: {error}"
        )


with export_col2:

    if st.button(
        "Generate Selected Period PDF",
        key="generate_period_pdf"
    ):

        try:

            pdf_bytes = create_pdf_report(
                current_data,
                current_kpis,
                previous_kpis,
                start_date,
                end_date,
                previous_start,
                previous_end
            )

            st.session_state[
                "period_pdf_bytes"
            ] = pdf_bytes

            st.session_state[
                "period_pdf_filename"
            ] = f"{period_filename}.pdf"

        except Exception as error:

            st.error(
                f"PDF export failed: {error}"
            )


if "period_pdf_bytes" in st.session_state:

    st.download_button(
        label="Download Selected Period PDF",

        data=st.session_state[
            "period_pdf_bytes"
        ],

        file_name=st.session_state[
            "period_pdf_filename"
        ],

        mime="application/pdf",

        key="download_period_pdf"
    )


# ============================================================
# 14. EXISTING WEEKLY REPORT ARCHIVES
# ============================================================

st.divider()

st.markdown(
    "### Download Existing Weekly Reports"
)

latest_excel_path = (
    REPORTS_DIR
    / "FitCore_Weekly_Business_Report.xlsx"
)

latest_pdf_path = (
    REPORTS_DIR
    / "FitCore_Weekly_Business_Report.pdf"
)

latest_col1, latest_col2 = st.columns(2)


with latest_col1:

    if latest_excel_path.exists():

        with open(
            latest_excel_path,
            "rb"
        ) as file:

            st.download_button(
                "Download Latest Weekly Excel",

                data=file.read(),

                file_name=latest_excel_path.name,

                mime=(
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),

                key="download_latest_weekly_excel"
            )

    else:

        st.info(
            "Latest weekly Excel report not found."
        )


with latest_col2:

    if latest_pdf_path.exists():

        with open(
            latest_pdf_path,
            "rb"
        ) as file:

            st.download_button(
                "Download Latest Weekly PDF",

                data=file.read(),

                file_name=latest_pdf_path.name,

                mime="application/pdf",

                key="download_latest_weekly_pdf"
            )

    else:

        st.info(
            "Latest weekly PDF report not found."
        )


week_pattern = re.compile(
    r"^FitCore_Weekly_Business_Report_"
    r"(\d{4}-W\d{2})\.(xlsx|pdf)$",
    re.IGNORECASE
)

weekly_archives = {}

if ARCHIVE_DIR.exists():

    for file_path in ARCHIVE_DIR.iterdir():

        if not file_path.is_file():
            continue

        match = week_pattern.match(
            file_path.name
        )

        if match:

            week_label = match.group(1)

            file_type = (
                match.group(2).lower()
            )

            weekly_archives.setdefault(
                week_label,
                {}
            )[file_type] = file_path


available_weeks = sorted(
    weekly_archives.keys(),
    reverse=True
)


if available_weeks:

    selected_archive_week = st.selectbox(
        "Select archived weekly report",

        available_weeks,

        key="existing_weekly_archive_selector"
    )

    selected_archive = weekly_archives[
        selected_archive_week
    ]

    archive_col1, archive_col2 = (
        st.columns(2)
    )


    with archive_col1:

        excel_path = selected_archive.get(
            "xlsx"
        )

        if excel_path and excel_path.exists():

            with open(
                excel_path,
                "rb"
            ) as file:

                st.download_button(
                    (
                        f"Download "
                        f"{selected_archive_week} Excel"
                    ),

                    data=file.read(),

                    file_name=excel_path.name,

                    mime=(
                        "application/"
                        "vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),

                    key=(
                        f"archive_excel_"
                        f"{selected_archive_week}"
                    )
                )


    with archive_col2:

        pdf_path = selected_archive.get(
            "pdf"
        )

        if pdf_path and pdf_path.exists():

            with open(
                pdf_path,
                "rb"
            ) as file:

                st.download_button(
                    (
                        f"Download "
                        f"{selected_archive_week} PDF"
                    ),

                    data=file.read(),

                    file_name=pdf_path.name,

                    mime="application/pdf",

                    key=(
                        f"archive_pdf_"
                        f"{selected_archive_week}"
                    )
                )

else:

    st.info(
        "No archived weekly reports found."
    )


# ============================================================
# 15. FOOTER
# ============================================================

st.divider()

st.caption(
    "FitCore Gym | Historical Business Intelligence, "
    "Reporting and Automation System"
)


# ============================================================
# FITCORE - MEMBER INACTIVITY INTELLIGENCE DASHBOARD
# ============================================================

st.divider()
st.header("Member Inactivity Intelligence")

st.caption(
    "Predictive analytics for identifying members who may "
    "stop attending the gym during the next 30 days."
)

# ------------------------------------------------------------
# 1. LOAD LATEST PREDICTIONS FROM POSTGRESQL
# ------------------------------------------------------------

from sqlalchemy import text

@st.cache_data(ttl=300)
def load_inactivity_predictions():

    query = text("""
        SELECT
            member_id,
            as_of_date,
            inactivity_probability,
            risk_band,
            predicted_inactivity
        FROM public.fitcore_inactivity_predictions
        WHERE as_of_date = (
            SELECT MAX(as_of_date)
            FROM public.fitcore_inactivity_predictions
        )
        ORDER BY inactivity_probability DESC
    """)

    with engine.connect() as conn:
        return pd.read_sql(query, conn)


try:
    risk_df = load_inactivity_predictions()

except Exception as e:
    st.error(f"Unable to load inactivity predictions: {e}")
    risk_df = pd.DataFrame()


# ------------------------------------------------------------
# 2. DASHBOARD KPIs
# ------------------------------------------------------------

if not risk_df.empty:

    risk_df["as_of_date"] = pd.to_datetime(
        risk_df["as_of_date"]
    )

    total_scored = len(risk_df)

    higher_risk = (
        risk_df["risk_band"] == "Higher"
    ).sum()

    lower_risk = (
        risk_df["risk_band"] == "Lower"
    ).sum()

    higher_risk_pct = (
        higher_risk / total_scored * 100
    )

    scoring_date = risk_df["as_of_date"].max().date()

    st.info(
        f"Predictions generated using data through "
        f"{scoring_date}. These are not necessarily "
        f"current-day predictions."
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Members Scored", total_scored)

    col2.metric("Higher Risk", int(higher_risk))

    col3.metric("Lower Risk", int(lower_risk))

    col4.metric(
        "Higher Risk %",
        f"{higher_risk_pct:.1f}%"
    )

    # --------------------------------------------------------
    # 3. RISK DISTRIBUTION
    # --------------------------------------------------------

    st.subheader("Risk Distribution")

    risk_counts = (
        risk_df["risk_band"]
        .value_counts()
        .reset_index()
    )

    risk_counts.columns = [
        "Risk Level",
        "Members"
    ]

    import plotly.express as px

    fig = px.bar(
        risk_counts,
        x="Risk Level",
        y="Members",
        color="Risk Level",
        color_discrete_map={
            "Higher": "#E74C3C",
            "Lower": "#2ECC71"
        },
        text="Members"
    )

    fig.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="Number of Members"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # 4. HIGHER-RISK MEMBER TABLE
    # --------------------------------------------------------

    st.subheader("Members Requiring Attention")

    high_risk_df = risk_df[
        risk_df["risk_band"] == "Higher"
    ].copy()

    high_risk_df["Risk Score (%)"] = (
        high_risk_df["inactivity_probability"] * 100
    ).round(2)

    st.dataframe(
        high_risk_df[
            [
                "member_id",
                "Risk Score (%)",
                "risk_band"
            ]
        ].rename(
            columns={
                "member_id": "Member ID",
                "risk_band": "Risk Level"
            }
        ),
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # 5. INDIVIDUAL MEMBER RISK LOOKUP
    # --------------------------------------------------------

    st.subheader("Individual Member Risk")

    selected_member = st.selectbox(
        "Select a member",
        risk_df["member_id"].tolist()
    )

    member_risk = risk_df[
        risk_df["member_id"] == selected_member
    ].iloc[0]

    st.metric(
        "Estimated Inactivity Risk Score",
        f"{member_risk['inactivity_probability'] * 100:.2f}%"
    )

    st.write(
        "Risk category:",
        member_risk["risk_band"]
    )

    # --------------------------------------------------------
    # 6. EXPORT PREDICTIONS
    # --------------------------------------------------------

    st.subheader("Export Risk Predictions")

    csv_data = risk_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Inactivity Predictions (CSV)",
        data=csv_data,
        file_name=(
            f"fitcore_inactivity_predictions_"
            f"{scoring_date}.csv"
        ),
        mime="text/csv"
    )

else:

    st.warning(
        "No inactivity predictions are available. "
        "Run the ML scoring pipeline first."
    )
