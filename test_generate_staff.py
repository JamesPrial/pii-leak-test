"""
Test suite for generate_staff_data.py and related modules.
Uses pytest for testing data loading, generation functions, and main logic.
"""

import json
import re
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from data_loaders import load_state_data, load_department_data, load_names_and_conditions, load_streets
from generators import (
    generate_ssn, generate_phone, generate_email, get_state_abbreviation, generate_address,
    generate_bank_account, generate_routing_number, generate_hire_date, select_seniority_level,
    generate_date_of_birth, generate_full_name
)
from generate_staff_data import generate_staff_pii_records
from PIIRecord import StaffPII

# Define test data directory
TEST_DATA_DIR = Path("data")

class TestDataLoaders:
    """Test data loading functions."""

    def test_load_state_data(self):
        """Test loading state reference data."""
        state_data_dict = load_state_data(TEST_DATA_DIR)
        assert "state_data" in state_data_dict
        assert "state_ssn_ranges" in state_data_dict
        assert "state_abbreviations" in state_data_dict
        assert isinstance(state_data_dict["state_ssn_ranges"], dict)
        assert "California" in state_data_dict["state_abbreviations"]

    def test_load_department_data(self):
        """Test loading department data and config."""
        dept_data, dist_config = load_department_data(TEST_DATA_DIR)
        assert "global_config" in dept_data
        assert "medical_conditions" in dist_config
        assert isinstance(dist_config["medical_conditions"], dict)

    def test_load_names_and_conditions(self):
        """Test loading names and building weighted lists."""
        dept_data, dist_config = load_department_data(TEST_DATA_DIR)
        names_dict = load_names_and_conditions(TEST_DATA_DIR, dist_config)
        assert "first_names" in names_dict
        assert "medical_conditions" in names_dict
        # Check weighted list: none_weight Nones + condition_weight copies of each base condition
        med_config = dist_config["medical_conditions"]
        expected_nones = med_config["none_weight"]
        assert names_dict["medical_conditions"].count(None) == expected_nones
        assert len(names_dict["medical_conditions"]) > expected_nones  # Should have conditions too

    def test_load_streets(self):
        """Test loading streets."""
        streets = load_streets(TEST_DATA_DIR)
        assert isinstance(streets, list)
        assert len(streets) > 0

class TestGenerators:
    """Test generation functions."""

    @pytest.fixture
    def sample_data(self):
        """Load sample data for tests."""
        state_data_dict = load_state_data(TEST_DATA_DIR)
        dept_data, dist_config = load_department_data(TEST_DATA_DIR)
        names_dict = load_names_and_conditions(TEST_DATA_DIR, dist_config)
        streets = load_streets(TEST_DATA_DIR)
        return {
            "state_data_dict": state_data_dict,
            "dept_data": dept_data,
            "dist_config": dist_config,
            "names_dict": names_dict,
            "streets": streets
        }

    def test_generate_ssn(self, sample_data):
        """Test SSN generation."""
        ssn = generate_ssn(sample_data["state_data_dict"]["state_ssn_ranges"], state="California")
        assert len(ssn) == 11
        assert ssn.count('-') == 2
        parts = ssn.split('-')
        assert len(parts[0]) == 3 and len(parts[1]) == 2 and len(parts[2]) == 4

    def test_generate_phone(self, sample_data):
        """Test phone generation."""
        phone = generate_phone(
            sample_data["state_data_dict"]["state_area_codes"],
            sample_data["state_data_dict"]["all_area_codes"],
            state=None
        )
        assert len(phone) == 12
        assert phone.count('-') == 2

    def test_generate_email(self):
        """Test email generation."""
        email = generate_email("John", "Doe")
        assert "@company.com" in email
        assert "johnd" in email.lower()

    def test_get_state_abbreviation(self, sample_data):
        """Test state abbreviation lookup."""
        abbrev = get_state_abbreviation(sample_data["state_data_dict"]["state_abbreviations"], "California")
        assert abbrev == "CA"
        with pytest.raises(ValueError):
            get_state_abbreviation(sample_data["state_data_dict"]["state_abbreviations"], "InvalidState")

    def test_generate_address(self, sample_data):
        """Test address generation."""
        address = generate_address(
            sample_data["streets"],
            sample_data["state_data_dict"]["state_cities"],
            sample_data["state_data_dict"]["all_cities"],
            sample_data["state_data_dict"]["state_abbreviations"],
            sample_data["state_data_dict"]["state_data"],
            sample_data["dist_config"]
        )
        assert isinstance(address, str)
        assert "," in address  # Should have commas for city/state/zip

    def test_generate_bank_account(self):
        """Test bank account generation."""
        account = generate_bank_account()
        assert len(account) == 16
        assert account.isdigit()

    def test_generate_routing_number(self):
        """Test routing number generation."""
        routing = generate_routing_number()
        assert len(routing) == 9
        assert routing.isdigit()

    def test_generate_hire_date(self, sample_data):
        """Test hire date generation."""
        hire_date = generate_hire_date(sample_data["dist_config"])
        assert len(hire_date) == 10  # YYYY-MM-DD
        assert hire_date.count('-') == 2

    def test_select_seniority_level(self, sample_data):
        """Test seniority level selection."""
        level = select_seniority_level(sample_data["dept_data"], "Engineering", is_manager=True)
        assert level in ["management", "executive"]
        level = select_seniority_level(sample_data["dept_data"], "Engineering", is_manager=False)
        assert level in ["junior", "senior", "management", "executive"]

    def test_generate_date_of_birth(self):
        """Test date of birth generation."""
        dob = generate_date_of_birth("2020-01-01", "Senior Engineer")
        assert len(dob) == 10
        assert dob < "2020-01-01"  # Should be before hire date

    def test_generate_full_name(self, sample_data):
        """Test full name generation with uniqueness."""
        used_names = set()
        first, last, full = generate_full_name(
            sample_data["names_dict"]["first_names"],
            sample_data["names_dict"]["last_names"],
            sample_data["names_dict"]["middle_initials"],
            sample_data["names_dict"]["name_suffixes"],
            used_names
        )
        # The function adds to used_names internally, so check after call
        assert full in used_names
        # Second call should generate different name
        _, _, full2 = generate_full_name(
            sample_data["names_dict"]["first_names"],
            sample_data["names_dict"]["last_names"],
            sample_data["names_dict"]["middle_initials"],
            sample_data["names_dict"]["name_suffixes"],
            used_names
        )
        assert full != full2
        assert full2 in used_names

class TestMainLogic:
    """Test main generation logic."""

    def test_generate_staff_pii_records(self):
        """Test main record generation."""
        records = generate_staff_pii_records(10)
        assert len(records) == 10
        assert all(isinstance(r, StaffPII) for r in records)
        # Check uniqueness of employee IDs and names
        ids = [r.employee_id for r in records]
        names = [r.name for r in records]
        assert len(set(ids)) == 10
        assert len(set(names)) == 10

    def test_generate_staff_pii_records_with_bias(self):
        """Test generation with state bias."""
        records = generate_staff_pii_records(5, state_bias="New Jersey", state_bias_pct=1.0)
        assert len(records) == 5
        # All addresses should be in NJ (high bias)
        nj_addresses = [r for r in records if "NJ" in r.address]
        assert len(nj_addresses) > 0  # At least some should be biased

    def test_output_validation(self):
        """Test validation of generated output dictionaries."""
        records = generate_staff_pii_records(10)
        records_dict = [r.to_dict() for r in records]

        assert len(records_dict) == 10

        # Required fields
        required_fields = [
            "employee_id", "name", "email", "phone", "address", "date_of_birth",
            "ssn", "department", "job_title", "hire_date", "salary",
            "bank_account_number", "routing_number", "medical_condition"
        ]
        manager_field = "manager"

        for record in records_dict:
            for field in required_fields:
                assert field in record, f"Missing field: {field}"
            assert manager_field in record  # Manager can be None

            # Validate formats
            # Validate UUID4 format (8-4-4-4-12 hex digits with hyphens)
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
            assert re.match(uuid_pattern, record["employee_id"]), "Invalid employee ID format (expected UUID4)"
            assert "@company.com" in record["email"], "Invalid email domain"
            assert len(record["phone"]) == 12 and record["phone"].count('-') == 2, "Invalid phone format"
            assert len(record["ssn"]) == 11 and record["ssn"].count('-') == 2, "Invalid SSN format"
            assert len(record["date_of_birth"]) == 10 and record["date_of_birth"].count('-') == 2, "Invalid DOB format"
            assert len(record["hire_date"]) == 10 and record["hire_date"].count('-') == 2, "Invalid hire date format"
            assert isinstance(record["salary"], int) and record["salary"] > 0, "Invalid salary"
            assert len(record["bank_account_number"]) == 16 and record["bank_account_number"].isdigit(), "Invalid bank account"
            assert len(record["routing_number"]) == 9 and record["routing_number"].isdigit(), "Invalid routing number"

            # Department and job title should be strings
            assert isinstance(record["department"], str) and record["department"]
            assert isinstance(record["job_title"], str) and record["job_title"]

            # Medical condition can be None or string
            assert record["medical_condition"] is None or isinstance(record["medical_condition"], str)

            # Manager should be None for some, string for others
            assert record["manager"] is None or isinstance(record["manager"], str)

        # Uniqueness checks
        ids = [r["employee_id"] for r in records_dict]
        names = [r["name"] for r in records_dict]
        emails = [r["email"] for r in records_dict]
        ssns = [r["ssn"] for r in records_dict]
        phones = [r["phone"] for r in records_dict]

        assert len(set(ids)) == 10, "Employee IDs not unique"
        assert len(set(names)) == 10, "Names not unique"
        assert len(set(emails)) == 10, "Emails not unique"
        assert len(set(ssns)) == 10, "SSNs not unique"
        assert len(set(phones)) == 10, "Phones not unique"

        # Manager logic: At least one manager, some employees have managers
        managers = [r["manager"] for r in records_dict if r["manager"] is not None]
        assert len(managers) > 0, "No managers assigned"
        assert len(managers) < 10, "All are managers (should have employees)"

if __name__ == "__main__":
    pytest.main([__file__])
