#!/usr/bin/env python3
"""
Generate realistic staff PII records for testing purposes.
Refactored for better modularity and readability.
"""

import argparse
import json
import logging
import random
import uuid
from pathlib import Path
from src.types import StaffPII
from .data_loaders import load_state_data, load_department_data, load_names_and_conditions, load_streets
from .generators import (
    generate_ssn, generate_phone, generate_email, get_state_abbreviation, generate_address,
    generate_bank_account, generate_routing_number, generate_hire_date, select_seniority_level,
    generate_date_of_birth, generate_full_name
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define data directory (relative to project root)
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Load all data using modular loaders
logger.info("Loading data files...")
state_data_dict = load_state_data(DATA_DIR)
dept_data, dist_config = load_department_data(DATA_DIR)
names_dict = load_names_and_conditions(DATA_DIR, dist_config)
streets = load_streets(DATA_DIR)

# Unpack loaded data for easy access
STATE_DATA = state_data_dict["state_data"]
STATE_SSN_RANGES = state_data_dict["state_ssn_ranges"]
STATE_ABBREVIATIONS = state_data_dict["state_abbreviations"]
STATE_AREA_CODES = state_data_dict["state_area_codes"]
STATE_CITIES = state_data_dict["state_cities"]
ALL_AREA_CODES = state_data_dict["all_area_codes"]
ALL_CITIES = state_data_dict["all_cities"]

FIRST_NAMES = names_dict["first_names"]
LAST_NAMES = names_dict["last_names"]
MEDICAL_CONDITIONS = names_dict["medical_conditions"]
NAME_SUFFIXES = names_dict["name_suffixes"]
MIDDLE_INITIALS = names_dict["middle_initials"]

STREETS = streets
NJ_STREETS = STREETS  # Backward compatibility


def generate_employee_details(department, seniority_level, is_manager, dist_config, dept_data, MEDICAL_CONDITIONS):
    """Generate common employee details: hire date, DOB, salary, medical condition."""
    hire_date = generate_hire_date(dist_config)
    date_of_birth = generate_date_of_birth(hire_date, random.choice(dept_data[department][seniority_level]["job_titles"]))

    salary_range = dept_data[department][seniority_level]["salary_range"]
    if is_manager:
        # Managers get higher end of salary range (upper 80% of range)
        range_size = salary_range[1] - salary_range[0]
        min_salary = int(salary_range[0] + range_size * 0.2)
        salary = random.randint(min_salary, salary_range[1])
    else:
        salary = random.randint(salary_range[0], salary_range[1])

    medical_condition = random.choice(MEDICAL_CONDITIONS)
    return hire_date, date_of_birth, salary, medical_condition


def create_staff_record(employee_id, first_name, last_name, full_name, department, seniority_level, is_manager, managers, state_bias, state_bias_pct):
    """Create a single StaffPII record."""
    job_title = random.choice(dept_data[department][seniority_level]["job_titles"])
    hire_date, date_of_birth, salary, medical_condition = generate_employee_details(department, seniority_level, is_manager, dist_config, dept_data, MEDICAL_CONDITIONS)

    record = StaffPII(
        employee_id=employee_id,
        name=full_name,
        email=generate_email(first_name, last_name, employee_id),
        phone=generate_phone(STATE_AREA_CODES, ALL_AREA_CODES, state=state_bias, bias_percentage=state_bias_pct),
        address=generate_address(STREETS, STATE_CITIES, ALL_CITIES, STATE_ABBREVIATIONS, STATE_DATA, dist_config, state=state_bias, bias_percentage=state_bias_pct),
        date_of_birth=date_of_birth,
        ssn=generate_ssn(STATE_SSN_RANGES, state=state_bias, bias_percentage=state_bias_pct),
        department=department,
        job_title=job_title,
        hire_date=hire_date,
        manager=None if is_manager else random.choice(managers),
        salary=salary,
        bank_account_number=generate_bank_account(),
        routing_number=generate_routing_number(),
        medical_condition=medical_condition
    )
    return record


def generate_staff_pii_records(count=50, state_bias=None, state_bias_pct=0.1):
    """Generate realistic staff PII records with configurable distributions.

    Args:
        count: Number of records to generate (default 50)
        state_bias: Optional state name to bias geographic data (default None = "New Jersey")
        state_bias_pct: Percentage bias for state-specific data 0.0-1.0 (default 0.1 = 10%)

    Returns:
        List of StaffPII records
    """
    logger.info(f"Generating {count} staff PII records...")

    records = []
    managers = []
    used_names = set()

    # Generate random employee IDs (UUID4)
    employee_ids = [str(uuid.uuid4()) for _ in range(count)]

    # First, create management positions
    # Ensure manager_count doesn't exceed total count
    manager_count = min(max(1, count // 10), count)
    logger.info(f"Creating {manager_count} manager records...")
    for i in range(manager_count):
        first_name, last_name, full_name = generate_full_name(FIRST_NAMES, LAST_NAMES, MIDDLE_INITIALS, NAME_SUFFIXES, used_names)

        # Select department (excluding global_config key)
        dept_names = [k for k in dept_data.keys() if k != "global_config"]
        department = random.choice(dept_names)

        # Select a management or executive level for managers
        seniority_level = select_seniority_level(dept_data, department, is_manager=True)

        record = create_staff_record(employee_ids[i], first_name, last_name, full_name, department, seniority_level, is_manager=True, managers=[], state_bias=state_bias, state_bias_pct=state_bias_pct)
        records.append(record)
        managers.append(employee_ids[i])

    # Create remaining employees with manager assignments
    remaining_count = count - manager_count
    logger.info(f"Creating {remaining_count} employee records...")
    for i in range(manager_count, count):
        first_name, last_name, full_name = generate_full_name(FIRST_NAMES, LAST_NAMES, MIDDLE_INITIALS, NAME_SUFFIXES, used_names)

        # Select department (excluding global_config key)
        dept_names = [k for k in dept_data.keys() if k != "global_config"]
        department = random.choice(dept_names)

        # Select a seniority level for regular employees
        seniority_level = select_seniority_level(dept_data, department, is_manager=False)

        record = create_staff_record(employee_ids[i], first_name, last_name, full_name, department, seniority_level, is_manager=False, managers=managers, state_bias=state_bias, state_bias_pct=state_bias_pct)
        records.append(record)

    # Shuffle records to avoid sequential ordering
    random.shuffle(records)
    logger.info(f"Generated {len(records)} records successfully.")
    return records

def main():
    """Generate staff records and write to JSON file with CLI argument support."""
    parser = argparse.ArgumentParser(
        description="Generate realistic staff PII records for testing purposes."
    )
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=50,
        help="Number of staff records to generate (default: 50)"
    )
    parser.add_argument(
        "-o", "--output-file",
        type=str,
        default="../../synth/test_staff_records.json",
        help="Output file path for generated records (default: synth/test_staff_records.json)"
    )

    args = parser.parse_args()

    logger.info("Starting staff PII record generation...")
    records = generate_staff_pii_records(args.count)

    # Convert records to dictionaries
    records_dict = [record.to_dict() for record in records]

    # Ensure output directory exists
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON file
    with open(args.output_file, "w") as f:
        json.dump(records_dict, f, indent=2)

    logger.info(f"Successfully generated {len(records)} staff records and written to {args.output_file}")
    logger.info("Sample record:")
    logger.info(json.dumps(records_dict[0], indent=2))

if __name__ == "__main__":
    main()
