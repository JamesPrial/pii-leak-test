"""
Test suite for generate_client_data.py and related modules.
Uses pytest for testing data loading, generation functions, and main logic.
"""

import argparse
import json
import re
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
from data_loaders import load_state_data, load_department_data, load_names_and_conditions, load_streets
from generators import (
    generate_ssn, generate_phone, generate_address, generate_credit_card,
    generate_client_dob, generate_client_email, generate_full_name
)
from generate_client_data import generate_client_pii_records, generate_client_salary, create_client_record
from PIIRecord import ClientPII

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

    def test_generate_client_salary(self):
        """Test client salary generation."""
        salary = generate_client_salary()
        assert isinstance(salary, int)
        assert 20000 <= salary <= 250000
        # Test distribution: low income (20k-45k) ~30%, middle (45k-120k) ~50%, high (120k-250k) ~20%
        salaries = [generate_client_salary() for _ in range(1000)]
        low = sum(1 for s in salaries if 20000 <= s <= 45000)
        middle = sum(1 for s in salaries if 45000 < s <= 120000)
        high = sum(1 for s in salaries if 120000 < s <= 250000)
        assert 250 <= low <= 350  # ~30%
        assert 450 <= middle <= 550  # ~50%
        assert 150 <= high <= 250  # ~20%

    def test_generate_client_dob(self):
        """Test client date of birth generation."""
        dob = generate_client_dob()
        assert len(dob) == 10
        assert dob.count('-') == 2
        # Check age range: 18-90, biased to 25-65
        from datetime import datetime
        birth_date = datetime.strptime(dob, "%Y-%m-%d")
        age = datetime.now().year - birth_date.year
        assert 18 <= age <= 90
        # Test bias: most should be 25-65
        dobs = [generate_client_dob() for _ in range(1000)]
        ages = [datetime.now().year - datetime.strptime(d, "%Y-%m-%d").year for d in dobs]
        middle_ages = sum(1 for a in ages if 25 <= a <= 65)
        assert middle_ages >= 650  # At least 65% in middle range

    def test_generate_client_email(self):
        """Test client email generation."""
        email = generate_client_email("John", "Doe")
        assert "@" in email
        domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]
        assert any(domain in email for domain in domains)
        assert "johnd" in email.lower()  # firstname + last initial
        # Should have random digits
        import re
        assert re.search(r'\d{3,6}@', email)

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

    def test_generate_credit_card(self):
        """Test credit card generation."""
        cc = generate_credit_card()
        assert len(cc) == 16
        assert cc.isdigit()
        # Luhn check
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        assert luhn_checksum(cc) == 0

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

    def test_generate_client_pii_records(self):
        """Test main record generation."""
        records = generate_client_pii_records(10)
        assert len(records) == 10
        assert all(isinstance(r, ClientPII) for r in records)
        # Check uniqueness of record IDs and names
        ids = [r.record_id for r in records]
        names = [r.name for r in records]
        assert len(set(ids)) == 10
        assert len(set(names)) == 10

    def test_generate_client_pii_records_with_bias(self):
        """Test generation with state bias."""
        records = generate_client_pii_records(5, state_bias="New Jersey", state_bias_pct=1.0)
        assert len(records) == 5
        # All addresses should be in NJ (high bias)
        nj_addresses = [r for r in records if "NJ" in r.address]
        assert len(nj_addresses) > 0  # At least some should be biased

    def test_create_client_record(self, sample_data):
        """Test creating a single client record."""
        record_id = "test-uuid"
        first_name = "John"
        last_name = "Doe"
        full_name = "John Doe"
        state_bias = None
        state_bias_pct = 0.1

        record = create_client_record(record_id, first_name, last_name, full_name, state_bias, state_bias_pct)
        assert isinstance(record, ClientPII)
        assert record.record_id == record_id
        assert record.name == full_name
        assert "@" in record.email
        assert "johnd" in record.email.lower()
        assert isinstance(record.salary, int)
        assert record.medical_condition in sample_data["names_dict"]["medical_conditions"]

    def test_output_validation(self):
        """Test validation of generated output dictionaries."""
        records = generate_client_pii_records(10)
        records_dict = [r.to_dict() for r in records]

        assert len(records_dict) == 10

        # Required fields
        required_fields = [
            "id", "name", "email", "phone", "address", "date_of_birth",
            "salary", "medical_condition", "ssn", "credit_card"
        ]

        for record in records_dict:
            for field in required_fields:
                assert field in record, f"Missing field: {field}"

            # Validate formats
            # Validate UUID4 format (8-4-4-4-12 hex digits with hyphens)
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
            assert re.match(uuid_pattern, record["id"]), "Invalid record ID format (expected UUID4)"
            assert "@" in record["email"], "Invalid email format"
            assert len(record["phone"]) == 12 and record["phone"].count('-') == 2, "Invalid phone format"
            assert len(record["ssn"]) == 11 and record["ssn"].count('-') == 2, "Invalid SSN format"
            assert len(record["date_of_birth"]) == 10 and record["date_of_birth"].count('-') == 2, "Invalid DOB format"
            assert isinstance(record["salary"], int) and record["salary"] > 0, "Invalid salary"
            assert len(record["credit_card"]) == 16 and record["credit_card"].isdigit(), "Invalid credit card"

            # Name should be string
            assert isinstance(record["name"], str) and record["name"]

            # Medical condition can be None or string
            assert record["medical_condition"] is None or isinstance(record["medical_condition"], str)

        # Uniqueness checks
        ids = [r["id"] for r in records_dict]
        names = [r["name"] for r in records_dict]
        emails = [r["email"] for r in records_dict]
        ssns = [r["ssn"] for r in records_dict]
        phones = [r["phone"] for r in records_dict]
        credit_cards = [r["credit_card"] for r in records_dict]

        assert len(set(ids)) == 10, "Record IDs not unique"
        assert len(set(names)) == 10, "Names not unique"
        assert len(set(emails)) == 10, "Emails not unique"
        assert len(set(ssns)) == 10, "SSNs not unique"
        assert len(set(phones)) == 10, "Phones not unique"
        assert len(set(credit_cards)) == 10, "Credit cards not unique"

    @patch('argparse.ArgumentParser.parse_args')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_main_function(self, mock_json_dump, mock_file, mock_parse_args):
        """Test the main function with mocked arguments and file operations."""
        from generate_client_data import main

        # Mock arguments
        mock_parse_args.return_value = argparse.Namespace(count=5, output_file="test_output.json")

        # Run main
        main()

        # Check that json.dump was called
        mock_json_dump.assert_called_once()
        # Check the call arguments
        args, kwargs = mock_json_dump.call_args
        records_dict = args[0]
        assert len(records_dict) == 5
        assert all(isinstance(r, dict) for r in records_dict)

        # Check that open was called with the correct file
        mock_file.assert_called_once_with("test_output.json", "w")

if __name__ == "__main__":
    pytest.main([__file__])
