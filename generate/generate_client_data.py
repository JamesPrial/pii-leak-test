#!/usr/bin/env python3
"""
Generate realistic client PII records for testing purposes.
Based on staff data generator but adapted for customer/client records.
"""

import argparse
import json
import logging
import random
import uuid
from pathlib import Path
from PIIRecord import ClientPII
from data_loaders import load_state_data, load_department_data, load_names_and_conditions, load_streets
from generators import (
    generate_ssn, generate_phone, generate_address, generate_credit_card,
    generate_client_dob, generate_client_email, generate_full_name
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define data directory
DATA_DIR = Path("data")

# Load all data using modular loaders
logger.info("Loading data files...")
state_data_dict = load_state_data(DATA_DIR)
dept_data, dist_config = load_department_data(DATA_DIR)  # Reuse global_config from departments.json
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


def generate_client_salary():
    """Generate a realistic annual income for a client.

    Uses realistic income distribution:
    - 30% low income: $20k-$45k
    - 50% middle income: $45k-$120k
    - 20% high income: $120k-$250k
    """
    income_tier = random.random()
    if income_tier < 0.3:  # Low income
        return random.randint(20000, 45000)
    elif income_tier < 0.8:  # Middle income
        return random.randint(45000, 120000)
    else:  # High income
        return random.randint(120000, 250000)


def create_client_record(record_id, first_name, last_name, full_name, state_bias, state_bias_pct):
    """Create a single ClientPII record."""
    record = ClientPII(
        record_id=record_id,
        name=full_name,
        email=generate_client_email(first_name, last_name),
        phone=generate_phone(STATE_AREA_CODES, ALL_AREA_CODES, state=state_bias, bias_percentage=state_bias_pct),
        address=generate_address(STREETS, STATE_CITIES, ALL_CITIES, STATE_ABBREVIATIONS, STATE_DATA, dist_config, state=state_bias, bias_percentage=state_bias_pct),
        date_of_birth=generate_client_dob(),
        salary=generate_client_salary(),
        medical_condition=random.choice(MEDICAL_CONDITIONS),
        ssn=generate_ssn(STATE_SSN_RANGES, state=state_bias, bias_percentage=state_bias_pct),
        credit_card=generate_credit_card()
    )
    return record


def generate_client_pii_records(count=50, state_bias=None, state_bias_pct=0.1):
    """Generate realistic client PII records with configurable distributions.

    Args:
        count: Number of records to generate (default 50)
        state_bias: Optional state name to bias geographic data (default None = "New Jersey")
        state_bias_pct: Percentage bias for state-specific data 0.0-1.0 (default 0.1 = 10%)

    Returns:
        List of ClientPII records
    """
    logger.info(f"Generating {count} client PII records...")

    records = []
    used_names = set()

    # Generate UUID record IDs
    record_ids = [str(uuid.uuid4()) for _ in range(count)]

    # Create client records
    logger.info(f"Creating {count} client records...")
    for i in range(count):
        first_name, last_name, full_name = generate_full_name(FIRST_NAMES, LAST_NAMES, MIDDLE_INITIALS, NAME_SUFFIXES, used_names)

        record = create_client_record(record_ids[i], first_name, last_name, full_name, state_bias, state_bias_pct)
        records.append(record)

    # Shuffle records to avoid sequential ordering
    random.shuffle(records)
    logger.info(f"Generated {len(records)} records successfully.")
    return records


def main():
    """Generate client records and write to JSON file with CLI argument support."""
    parser = argparse.ArgumentParser(
        description="Generate realistic client PII records for testing purposes."
    )
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=50,
        help="Number of client records to generate (default: 50)"
    )
    parser.add_argument(
        "-o", "--output-file",
        type=str,
        default="../synth/client_records.json",
        help="Output file path for generated records (default: synth/client_records.json)"
    )

    args = parser.parse_args()

    logger.info("Starting client PII record generation...")
    records = generate_client_pii_records(args.count)

    # Convert records to dictionaries
    records_dict = [record.to_dict() for record in records]

    # Ensure output directory exists
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON file
    with open(args.output_file, "w") as f:
        json.dump(records_dict, f, indent=2)

    logger.info(f"Successfully generated {len(records)} client records and written to {args.output_file}")
    logger.info("Sample record:")
    logger.info(json.dumps(records_dict[0], indent=2))


if __name__ == "__main__":
    main()
