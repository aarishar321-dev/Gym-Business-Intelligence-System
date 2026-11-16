from pathlib import Path
import pandas as pd

# Find the project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Names of the six CSV datasets
tables = [
    "members",
    "memberships",
    "attendance",
    "payments",
    "leads",
    "followups"
]

# Inspect the columns in each CSV
for table in tables:
    csv_path = PROJECT_ROOT / "data" / "processed" / f"{table}.csv"

    df = pd.read_csv(csv_path, nrows=0)

    print(f"\n{table}.csv")
    print(df.columns.tolist())