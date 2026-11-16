# Gym Business Intelligence & Predictive Analytics System

An end-to-end, data-driven solution designed to help gym businesses monitor operations, analyze performance, automate weekly reporting, and identify members at risk of inactivity using machine learning.

The system brings together **Python, synthetic business-data generation, PostgreSQL, ETL pipelines, SQL analytics, Streamlit dashboards, automated Excel/PDF reporting, and predictive analytics** in one business intelligence workflow.

---

## Project Overview

Managing gym operations involves handling membership records, payments, attendance, leads, and customer activity. Analyzing this information manually can make it difficult for gym owners to identify business trends and take timely decisions.

This project addresses these challenges by developing a centralized business intelligence system that transforms operational data into meaningful insights.

A key part of the project is **synthetic gym-business data generation**. Since a meaningful business intelligence and machine learning workflow requires a sufficiently large and varied dataset, Python scripts are used to generate structured sample records for core gym operations. The project also generates deliberately messy data to exercise and validate the data-cleaning and quality-checking workflow.

The generated data is processed through ETL pipelines, stored in PostgreSQL, analyzed using SQL, and presented through an interactive Streamlit dashboard. The system also incorporates machine learning to identify members who may be at risk of inactivity and generates weekly business reports in Excel and PDF formats.

> **Data note:** The operational datasets used for development and demonstration are synthetically generated. They are not presented as real customer or business records.

## Key Features

### 1. Synthetic Gym Business Data Generation

- Python-based generation of synthetic operational datasets to support development, testing, analytics, and machine learning.
- Generation scripts for key gym-business data, including attendance, leads, memberships, payments, and follow-ups.
- Generation of deliberately messy datasets to test data-cleaning and validation processes.
- Dataset validation scripts to check generated data and messy-data handling.
- Provides a larger and more varied data foundation for demonstrating business intelligence workflows without relying on real customer records.

### 2. Database Management

- PostgreSQL-based relational database.
- Structured storage of gym operational data.
- Database connectivity using SQLAlchemy and Psycopg2.
- Organized and reusable database operations.

### 3. ETL Pipeline

- Automated data extraction using Python.
- Data cleaning and transformation using Pandas and NumPy.
- Data validation and quality checks.
- Loading processed data into PostgreSQL.
- Structured data-processing workflow.

### 4. Business Analytics

- SQL-based business performance analysis.
- Membership and revenue analysis.
- Operational performance monitoring.
- Data-driven business insights.

### 5. Interactive Business Intelligence Dashboard

- Developed using Streamlit.
- Interactive visualizations using Plotly.
- Key Performance Indicator (KPI) monitoring.
- Monthly revenue analysis.
- Lead status and business performance visualization.

### 6. Automated Weekly Business Reporting

- Weekly report generation.
- Excel report generation using OpenPyXL and XlsxWriter.
- PDF report generation using ReportLab.
- Business performance summaries.
- Weekly report selection and review.

### 7. Machine Learning – Member Inactivity Prediction

- Machine learning-based inactivity prediction.
- Data preprocessing and feature preparation.
- Model development using Scikit-learn.
- Model serialization using Joblib.
- Prediction integration into the business intelligence workflow.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Database | PostgreSQL |
| Data Generation | Python-based synthetic data generation |
| Data Processing | Pandas, NumPy |
| ETL | Python |
| Database Connectivity | SQLAlchemy, Psycopg2 |
| Business Analytics | SQL |
| Dashboard | Streamlit |
| Data Visualization | Plotly, Matplotlib, Seaborn |
| Machine Learning | Scikit-learn |
| Model Persistence | Joblib |
| Excel Reporting | OpenPyXL, XlsxWriter |
| PDF Reporting | ReportLab |
| Environment Management | Python Virtual Environment, Python-dotenv |

---

## System Architecture

```text
             Synthetic Data Generation
                       |
          +------------+-------------+
          |                          |
          v                          v
   Structured Data              Messy Data
          |                          |
          +------------+-------------+
                       |
                       v
               Python ETL Pipeline
                       |
              Extract | Transform
                       |
                Data Validation
                       |
                       v
                  PostgreSQL
                       |
             SQL Business Analytics
                       |
          +------------+-------------+
          |            |              |
          v            v              v
      Streamlit     Machine         Weekly
      Dashboard     Learning       Reporting
          |            |              |
          v            v              v
      Business     Inactivity      Excel / PDF
      Insights     Prediction       Reports
```

---

## Project Structure

```text
gym-business-intelligence-system/
│
├── data/
│   ├── raw/
│   ├── messy/
│   └── processed/
│
├── notebooks/
│   └── Machine Learning Notebooks
│
├── reports/
│
├── src/
│   ├── dashboard/
│   ├── data_cleaning/
│   ├── data_generation/
│   │   ├── generate_data.py
│   │   ├── generate_attendance.py
│   │   ├── generate_followups.py
│   │   ├── generate_leads.py
│   │   ├── generate_memberships.py
│   │   ├── generate_messy_data.py
│   │   ├── generate_payments.py
│   │   ├── validate_dataset.py
│   │   └── validate_messy_data.py
│   ├── database/
│   ├── etl/
│   └── reporting/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

*The structure above represents the main project organization. Individual filenames and additional files may vary.*

---

# Installation and Setup Guide

Follow these instructions to set up and run the project locally.

## Prerequisites

Install the following software before proceeding:

1. **Python** – Install a compatible Python version.
   - https://www.python.org/downloads/

2. **PostgreSQL** – Required for database storage and operations.
   - https://www.postgresql.org/download/

3. **Git** – Required to clone the repository.
   - https://git-scm.com/downloads

4. **Visual Studio Code** (recommended).
   - https://code.visualstudio.com/

## Step 1: Clone the Repository

Open your terminal and execute:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Navigate into the project directory:

```bash
cd gym-business-intelligence-system
```

## Step 2: Create a Python Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

For macOS/Linux:

```bash
source .venv/bin/activate
```

## Step 3: Install Python Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Step 4: Configure PostgreSQL

1. Install PostgreSQL using the official installer.
2. Configure your PostgreSQL username and password.
3. Open pgAdmin or the PostgreSQL command-line interface.
4. Create a new database for the project.

Example using SQL:

```sql
CREATE DATABASE gym_business_db;
```

The database name above is an example. Use the database name expected by your project configuration.

## Step 5: Configure Environment Variables

Create a `.env` file in the project root directory.

Use the `.env.example` file as a reference and enter your local PostgreSQL connection details.

Example configuration:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gym_business_db
DB_USER=postgres
DB_PASSWORD=your_local_password
```

**Important:** These variable names are illustrative. Match them to the actual variable names used by the project's database connection code.

Never upload your `.env` file or actual database credentials to GitHub.

## Step 6: Generate the Synthetic Datasets

The project includes Python scripts in `src/data_generation/` for generating synthetic gym-business data.

These scripts cover operational areas such as:

- Attendance
- Leads
- Memberships
- Payments
- Follow-ups

The project also includes scripts for generating deliberately messy data and validating both the generated dataset and messy-data handling.

Review the scripts in `src/data_generation/` and execute the relevant generation and validation scripts using the project environment. Use the generated datasets as inputs for the ETL workflow.

## Step 7: Initialize the Database

Execute the project's database initialization or schema-creation scripts.

Ensure the required tables and relationships are created before running the ETL pipeline.

Refer to the `src/database/` directory for the database implementation.

## Step 8: Run the ETL Pipeline

Execute the project's Python ETL entry point to:

1. Extract source data.
2. Clean and transform the data.
3. Perform validation.
4. Load processed data into PostgreSQL.

Refer to the `src/etl/` directory for the actual execution entry point.

Verify that the expected records have been loaded into PostgreSQL.

## Step 9: Launch the Streamlit Dashboard

Run the dashboard entry-point script:

```bash
streamlit run path/to/your/dashboard_entry_point.py
```

Replace the example path with the actual dashboard script location.

The dashboard should open in your browser and display the available business intelligence metrics.

## Step 10: Generate Weekly Business Reports

Use the weekly reporting functionality to select and generate the required business performance report.

The reporting module supports:

- Weekly Excel reports.
- Weekly PDF reports.
- Business performance summaries.

Refer to `src/reporting/` for the implementation.

## Step 11: Explore Machine Learning Notebooks

Open the Jupyter notebooks inside the `notebooks/` directory.

These notebooks document the machine learning development and experimentation process, including data preparation, model development, and inactivity prediction.

Run them using Jupyter Notebook or VS Code with the required Python environment.

---

## Future Enhancements – Potential V2

The current release focuses on business intelligence, reporting automation, and predictive analytics.

Potential future extensions include:

- **WhatsApp Cloud API Integration:** Automated customer communication and enquiry handling.
- **AI-Powered Enquiry Chatbot:** Answer gym-related enquiries and provide membership information.
- **Automated Lead Management:** Lead capture, follow-ups, and conversion tracking.
- **Membership Lifecycle Automation:** Member registration, membership management, and payment workflows.
- **ML-Driven Retention Automation:** Use inactivity predictions to support targeted member engagement.
- **End-to-End Business Automation:** Connect customer acquisition, membership management, business intelligence, and retention workflows.

These are proposed enhancements and are not part of the current release.

---

## Project Status

**Version:** 1.0

**Release Scope:** Gym Business Intelligence & Predictive Analytics

The current version focuses on synthetic gym-business data generation, database management, ETL pipelines, business analytics, interactive dashboards, automated weekly reporting, and machine learning-based inactivity prediction.

---

## Author

**Aarish**

---

## License

See the repository's `LICENSE` file for licensing information.
