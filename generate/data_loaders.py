"""
Data loading utilities for staff PII generation.
Loads external data files and builds lookup tables.
"""

import json
from pathlib import Path

def load_state_data(data_dir: Path):
    """Load state reference data and build lookup tables."""
    with open(data_dir / "reference/state_reference_data.json", "r") as f:
        state_data = json.load(f)

    state_ssn_ranges = {state: data["ssn_ranges"] for state, data in state_data.items()}
    state_abbreviations = {state: data["state_abbrev"] for state, data in state_data.items()}
    state_area_codes = {
        state: [int(code) for code in data["area_codes"]]
        for state, data in state_data.items()
    }
    state_cities = {
        state: [(city["city"], zip_code)
                for city in data["cities"]
                for zip_code in city["zip_codes"]]
        for state, data in state_data.items()
    }
    all_area_codes = [code for codes in state_area_codes.values() for code in codes]
    all_cities = [(city, state_name) for state_name, cities in state_cities.items() for city in cities]

    return {
        "state_data": state_data,
        "state_ssn_ranges": state_ssn_ranges,
        "state_abbreviations": state_abbreviations,
        "state_area_codes": state_area_codes,
        "state_cities": state_cities,
        "all_area_codes": all_area_codes,
        "all_cities": all_cities,
    }

def load_department_data(data_dir: Path):
    """Load department data including global config."""
    with open(data_dir / "reference/departments.json", "r") as f:
        dept_data = json.load(f)
    dist_config = dept_data["global_config"]
    return dept_data, dist_config

def load_names_and_conditions(data_dir: Path, dist_config):
    """Load names, conditions, and build weighted lists."""
    # First names
    with open(data_dir / "sources/first_names.txt", "r") as f:
        first_names = [line.strip() for line in f if line.strip()]

    # Last names
    with open(data_dir / "sources/last_names.txt", "r") as f:
        last_names = [line.strip() for line in f if line.strip()]

    # Medical conditions: Build weighted list with None for no condition
    with open(data_dir / "sources/medical_conditions.txt", "r") as f:
        base_conditions = [line.strip() for line in f if line.strip()]
    med_config = dist_config["medical_conditions"]
    # Weighting: none_weight entries of None, plus condition_weight copies of each base condition
    medical_conditions = [None] * med_config["none_weight"] + base_conditions * med_config["condition_weight"]

    # Name suffixes: Build weighted list with empty string for no suffix
    with open(data_dir / "sources/name_suffixes.txt", "r") as f:
        base_suffixes = [line.strip() for line in f if line.strip()]
    suffix_config = dist_config["name_suffixes"]
    name_suffixes = [""] * suffix_config["none_weight"] + base_suffixes * suffix_config["suffix_weight"]

    # Middle initials: Build weighted list with empty string for no initial
    with open(data_dir / "sources/middle_initials.txt", "r") as f:
        base_initials = [line.strip() for line in f if line.strip()]
    initial_config = dist_config["middle_initials"]
    middle_initials = [""] * initial_config["none_weight"] + base_initials * initial_config["initial_weight"]

    return {
        "first_names": first_names,
        "last_names": last_names,
        "medical_conditions": medical_conditions,
        "name_suffixes": name_suffixes,
        "middle_initials": middle_initials,
    }

def load_streets(data_dir: Path):
    """Load street names."""
    with open(data_dir / "sources/streets.txt", "r") as f:
        streets = [line.strip() for line in f if line.strip()]
    return streets
