
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_DIR = Path(__file__).resolve().parents[2]
CLEANING_DIR = PROJECT_DIR / "src" / "data_cleaning"

# Cleaning and validation scripts
PIPELINE_STEPS = [
    ("Clean members", "clean_members.py"),
    ("Clean memberships", "clean_memberships.py"),
    ("Clean attendance", "clean_attendance.py"),
    ("Clean payments", "clean_payments.py"),
    ("Clean leads", "clean_leads.py"),
    ("Clean followups", "clean_followups.py"),
    ("Cross-table validation", "validate_cleaned_data.py")
]


def run_step(step_name, script_name):
    script_path = CLEANING_DIR / script_name

    print("\n" + "=" * 60)
    print(f"STEP: {step_name}")
    print("=" * 60)

    # Stop if the required script does not exist
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        return False

    # Execute the existing script using the active Python environment
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_DIR,
        check=False
    )

    # Stop the pipeline if the script fails
    if result.returncode != 0:
        print(f"\nFAILED: {step_name}")
        print(f"Exit code: {result.returncode}")
        return False

    print(f"\nSUCCESS: {step_name}")
    return True


def main():
    start_time = datetime.now()

    print("=" * 60)
    print("FITCORE GYM - ETL PIPELINE")
    print("=" * 60)

    print(f"Started at: {start_time:%Y-%m-%d %H:%M:%S}")
    print(f"Project directory: {PROJECT_DIR}")

    completed_steps = 0

    for step_name, script_name in PIPELINE_STEPS:

        success = run_step(step_name, script_name)

        if not success:
            print("\nETL PIPELINE STOPPED.")
            print("Fix the error before running it again.")
            sys.exit(1)

        completed_steps += 1

    end_time = datetime.now()
    duration = end_time - start_time

    print("\n" + "=" * 60)
    print("ETL PIPELINE COMPLETED")
    print("=" * 60)

    print(f"Successful steps: {completed_steps}")
    print(f"Started: {start_time:%Y-%m-%d %H:%M:%S}")
    print(f"Finished: {end_time:%Y-%m-%d %H:%M:%S}")
    print(f"Total duration: {duration}")

    print("\nValidated CSV files are available in:")
    print(PROJECT_DIR / "data" / "processed")


if __name__ == "__main__":
    main()