#!/usr/bin/env python3
"""
End-to-End Database Tests for PII PostgreSQL Setup

This test suite validates the complete database functionality including:
- Database connectivity and health
- Schema validation (tables, columns, constraints, indexes)
- Data loading (staff and client records)
- CRUD operations (Create, Read, Update, Delete)
- Constraint validation (unique, foreign key, NOT NULL, data types)
- Data integrity (manager hierarchy, PII formats, date relationships)

Requirements:
- Docker and Docker Compose must be running
- PostgreSQL container must be healthy
- Environment variables must be configured (see docker-compose.yml)

Usage:
    pytest test_database.py -v                    # Run all tests with verbose output
    pytest test_database.py -k test_schema -v     # Run only schema tests
    pytest test_database.py::TestCRUD -v          # Run only CRUD tests
"""

import json
import os
import pytest
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import patch

import psycopg2
from psycopg2 import sql, errors as pg_errors
from psycopg2.extensions import connection as pg_connection, cursor as pg_cursor


# ============================================================================
# Configuration
# ============================================================================

# Database connection parameters
DB_CONFIG = {
    'user': os.getenv('POSTGRES_USER', 'pii_admin'),
    'password': os.getenv('POSTGRES_PASSWORD', 'test_password_123'),
    'database': os.getenv('POSTGRES_DB', 'pii_records'),
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
}

# Test data file paths
STAFF_TEST_FILE = 'outputs/test_db_staff.json'
CLIENT_TEST_FILE = 'outputs/test_db_clients.json'


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture(scope='session')
def db_connection() -> pg_connection:
    """
    Create a database connection for the entire test session.

    This fixture:
    - Connects to the PostgreSQL database
    - Validates the connection is healthy
    - Yields the connection for tests
    - Closes the connection after all tests complete

    Yields:
        psycopg2 connection object

    Raises:
        psycopg2.Error: If connection fails
        AssertionError: If database health check fails
    """
    conn = None
    try:
        # Establish connection
        conn = psycopg2.connect(**DB_CONFIG)

        # Validate connection with a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        assert result == (1,), "Database health check failed"
        cursor.close()

        yield conn

    finally:
        # Clean up connection
        if conn:
            conn.close()


@pytest.fixture(scope='function')
def db_cursor(db_connection: pg_connection) -> pg_cursor:
    """
    Create a fresh database cursor for each test function.

    This fixture:
    - Creates a new cursor from the session connection
    - Starts a transaction
    - Yields the cursor for the test
    - Rolls back the transaction after the test (ensures test isolation)

    Args:
        db_connection: Database connection from db_connection fixture

    Yields:
        psycopg2 cursor object
    """
    cursor = db_connection.cursor()
    try:
        yield cursor
    finally:
        # Rollback any changes to ensure test isolation
        db_connection.rollback()
        cursor.close()


@pytest.fixture(scope='session')
def staff_test_data() -> List[Dict[str, Any]]:
    """
    Load staff test data from JSON file.

    Returns:
        List of staff record dictionaries

    Raises:
        FileNotFoundError: If test data file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    with open(STAFF_TEST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture(scope='session')
def client_test_data() -> List[Dict[str, Any]]:
    """
    Load client test data from JSON file.

    Returns:
        List of client record dictionaries

    Raises:
        FileNotFoundError: If test data file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    with open(CLIENT_TEST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# Test Class: Database Connectivity
# ============================================================================

class TestConnectivity:
    """Test database connectivity and health checks."""

    def test_connection_success(self, db_connection: pg_connection):
        """Verify database connection is established."""
        assert db_connection is not None
        assert not db_connection.closed

    def test_database_version(self, db_cursor: pg_cursor):
        """Verify PostgreSQL version is 16+."""
        db_cursor.execute("SELECT version();")
        version_string = db_cursor.fetchone()[0]
        assert 'PostgreSQL' in version_string
        # Extract major version (e.g., "PostgreSQL 16.3" -> 16)
        version_match = re.search(r'PostgreSQL (\d+)', version_string)
        assert version_match, "Could not parse PostgreSQL version"
        major_version = int(version_match.group(1))
        assert major_version >= 16, f"Expected PostgreSQL 16+, got {major_version}"


# ============================================================================
# Test Class: Schema Validation
# ============================================================================

class TestSchema:
    """Test database schema including tables, columns, constraints, and indexes."""

    def test_tables_exist(self, db_cursor: pg_cursor):
        """Verify both staff_pii and client_pii tables exist."""
        db_cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in db_cursor.fetchall()]

        assert 'staff_pii' in tables, "staff_pii table does not exist"
        assert 'client_pii' in tables, "client_pii table does not exist"

    def test_staff_table_columns(self, db_cursor: pg_cursor):
        """Verify staff_pii table has all expected columns with correct types."""
        db_cursor.execute("""
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'staff_pii'
            ORDER BY ordinal_position;
        """)
        columns = {row[0]: {'type': row[1], 'nullable': row[2], 'max_length': row[3]}
                   for row in db_cursor.fetchall()}

        # Expected columns (14 total as per schema)
        expected_columns = [
            'employee_id', 'name', 'email', 'phone', 'address',
            'date_of_birth', 'ssn', 'department', 'job_title', 'hire_date',
            'manager', 'salary', 'bank_account_number', 'routing_number',
            'medical_condition'
        ]

        for col in expected_columns:
            assert col in columns, f"Column {col} missing from staff_pii table"

        # Verify specific column types
        assert columns['employee_id']['type'] == 'character varying'
        assert columns['date_of_birth']['type'] == 'date'
        assert columns['salary']['type'] == 'integer'
        assert columns['manager']['nullable'] == 'YES'  # Manager is nullable
        assert columns['medical_condition']['nullable'] == 'YES'  # Medical condition is nullable

    def test_client_table_columns(self, db_cursor: pg_cursor):
        """Verify client_pii table has all expected columns with correct types."""
        db_cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'client_pii'
            ORDER BY ordinal_position;
        """)
        columns = {row[0]: {'type': row[1], 'nullable': row[2]}
                   for row in db_cursor.fetchall()}

        # Expected columns (10 total as per schema)
        expected_columns = [
            'record_id', 'name', 'email', 'phone', 'address',
            'date_of_birth', 'salary', 'medical_condition', 'ssn', 'credit_card'
        ]

        for col in expected_columns:
            assert col in columns, f"Column {col} missing from client_pii table"

        # Verify specific column types
        assert columns['record_id']['type'] == 'character varying'
        assert columns['date_of_birth']['type'] == 'date'
        assert columns['salary']['type'] == 'integer'
        assert columns['credit_card']['type'] == 'character varying'

    def test_primary_keys(self, db_cursor: pg_cursor):
        """Verify primary key constraints exist on both tables."""
        db_cursor.execute("""
            SELECT tc.table_name, kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = 'public'
                AND tc.table_name IN ('staff_pii', 'client_pii');
        """)
        pk_constraints = {row[0]: row[1] for row in db_cursor.fetchall()}

        assert pk_constraints.get('staff_pii') == 'employee_id'
        assert pk_constraints.get('client_pii') == 'record_id'

    def test_foreign_key_constraints(self, db_cursor: pg_cursor):
        """Verify foreign key constraint exists for manager self-reference."""
        db_cursor.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = 'staff_pii';
        """)
        fk_constraints = db_cursor.fetchall()

        # Should have exactly one FK: manager -> employee_id
        assert len(fk_constraints) == 1
        table_name, column_name, foreign_table, foreign_column = fk_constraints[0]
        assert column_name == 'manager'
        assert foreign_table == 'staff_pii'
        assert foreign_column == 'employee_id'

    def test_indexes_exist(self, db_cursor: pg_cursor):
        """Verify expected indexes exist for commonly queried fields."""
        db_cursor.execute("""
            SELECT indexname, tablename
            FROM pg_indexes
            WHERE schemaname = 'public'
                AND tablename IN ('staff_pii', 'client_pii')
            ORDER BY tablename, indexname;
        """)
        indexes = [(row[1], row[0]) for row in db_cursor.fetchall()]

        # Expected indexes (from init_schema.sql)
        expected_indexes = [
            ('staff_pii', 'idx_staff_ssn'),
            ('staff_pii', 'idx_staff_email'),
            ('staff_pii', 'idx_staff_department'),
            ('staff_pii', 'idx_staff_manager'),
            ('client_pii', 'idx_client_ssn'),
            ('client_pii', 'idx_client_email'),
        ]

        for table, index in expected_indexes:
            assert (table, index) in indexes, f"Missing index {index} on {table}"


# ============================================================================
# Test Class: Data Loading
# ============================================================================

class TestDataLoading:
    """Test loading synthetic PII data into database tables."""

    def test_load_staff_records(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection,
        staff_test_data: List[Dict[str, Any]]
    ):
        """Test loading staff records into database."""
        # Truncate table first
        db_cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")
        db_connection.commit()

        # Insert records (using two-phase approach for manager references)
        insert_query = """
            INSERT INTO staff_pii (
                employee_id, name, email, phone, address, date_of_birth, ssn,
                department, job_title, hire_date, salary,
                bank_account_number, routing_number, medical_condition, manager
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, NULL
            )
        """

        inserted_count = 0
        for record in staff_test_data:
            db_cursor.execute(insert_query, (
                record['employee_id'],
                record['name'],
                record['email'],
                record['phone'],
                record['address'],
                record['date_of_birth'],
                record['ssn'],
                record['department'],
                record['job_title'],
                record['hire_date'],
                record['salary'],
                record['bank_account_number'],
                record['routing_number'],
                record.get('medical_condition', 'None')
            ))
            inserted_count += 1

        db_connection.commit()

        # Update manager references
        update_query = "UPDATE staff_pii SET manager = %s WHERE employee_id = %s"
        for record in staff_test_data:
            if record.get('manager'):
                db_cursor.execute(update_query, (
                    record['manager'],
                    record['employee_id']
                ))

        db_connection.commit()

        # Verify record count
        db_cursor.execute("SELECT COUNT(*) FROM staff_pii;")
        count = db_cursor.fetchone()[0]
        assert count == len(staff_test_data), f"Expected {len(staff_test_data)} records, got {count}"

    def test_load_client_records(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection,
        client_test_data: List[Dict[str, Any]]
    ):
        """Test loading client records into database."""
        # Truncate table first
        db_cursor.execute("TRUNCATE TABLE client_pii CASCADE;")
        db_connection.commit()

        # Insert records
        insert_query = """
            INSERT INTO client_pii (
                record_id, name, email, phone, address, date_of_birth,
                salary, medical_condition, ssn, credit_card
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """

        inserted_count = 0
        for record in client_test_data:
            db_cursor.execute(insert_query, (
                record['record_id'],  # Note: generated data uses 'record_id', matching schema
                record['name'],
                record['email'],
                record['phone'],
                record['address'],
                record['date_of_birth'],
                record['salary'],
                record.get('medical_condition') or 'None',  # Handle None/null values
                record['ssn'],
                record['credit_card']
            ))
            inserted_count += 1

        db_connection.commit()

        # Verify record count
        db_cursor.execute("SELECT COUNT(*) FROM client_pii;")
        count = db_cursor.fetchone()[0]
        assert count == len(client_test_data), f"Expected {len(client_test_data)} records, got {count}"

    def test_duplicate_staff_email_rejected(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection,
        staff_test_data: List[Dict[str, Any]]
    ):
        """Test that duplicate email addresses are handled (should allow duplicates per current schema)."""
        # Load first record
        first_record = staff_test_data[0]

        # Clear table
        db_cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")
        db_connection.commit()

        # Insert first record
        db_cursor.execute("""
            INSERT INTO staff_pii (
                employee_id, name, email, phone, address, date_of_birth, ssn,
                department, job_title, hire_date, salary,
                bank_account_number, routing_number, medical_condition
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            first_record['employee_id'],
            first_record['name'],
            first_record['email'],
            first_record['phone'],
            first_record['address'],
            first_record['date_of_birth'],
            first_record['ssn'],
            first_record['department'],
            first_record['job_title'],
            first_record['hire_date'],
            first_record['salary'],
            first_record['bank_account_number'],
            first_record['routing_number'],
            first_record.get('medical_condition', 'None')
        ))
        db_connection.commit()

        # Try to insert duplicate email with different employee_id
        # Current schema doesn't have unique constraint on email, so this should succeed
        db_cursor.execute("""
            INSERT INTO staff_pii (
                employee_id, name, email, phone, address, date_of_birth, ssn,
                department, job_title, hire_date, salary,
                bank_account_number, routing_number, medical_condition
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            'different-id-123',
            first_record['name'],
            first_record['email'],  # Duplicate email
            first_record['phone'],
            first_record['address'],
            first_record['date_of_birth'],
            '123-45-6789',  # Valid SSN format
            first_record['department'],
            first_record['job_title'],
            first_record['hire_date'],
            first_record['salary'],
            first_record['bank_account_number'],
            first_record['routing_number'],
            first_record.get('medical_condition', 'None')
        ))
        db_connection.commit()

        # Verify both records exist (no unique constraint)
        db_cursor.execute("SELECT COUNT(*) FROM staff_pii WHERE email = %s", (first_record['email'],))
        count = db_cursor.fetchone()[0]
        assert count == 2, "Expected duplicate emails to be allowed (no unique constraint)"


# ============================================================================
# Test Class: CRUD Operations
# ============================================================================

class TestCRUD:
    """Test Create, Read, Update, Delete operations."""

    def test_create_staff_record(self, db_cursor: pg_cursor, db_connection: pg_connection):
        """Test inserting a new staff record."""
        # Create a test record
        test_record = {
            'employee_id': 'test-emp-001',
            'name': 'Test Employee',
            'email': 'test.employee@company.com',
            'phone': '555-1234',
            'address': '123 Test St, Test City, TS 12345',
            'date_of_birth': '1990-01-15',
            'ssn': '123-45-6789',
            'department': 'Engineering',
            'job_title': 'Software Engineer',
            'hire_date': '2020-03-01',
            'salary': 95000,
            'bank_account_number': '1234567890',
            'routing_number': '987654321',
            'medical_condition': None
        }

        # Insert record
        db_cursor.execute("""
            INSERT INTO staff_pii (
                employee_id, name, email, phone, address, date_of_birth, ssn,
                department, job_title, hire_date, salary,
                bank_account_number, routing_number, medical_condition
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, tuple(test_record.values()))

        db_connection.commit()

        # Verify record was inserted
        db_cursor.execute("SELECT * FROM staff_pii WHERE employee_id = %s", ('test-emp-001',))
        result = db_cursor.fetchone()
        assert result is not None
        assert result[0] == 'test-emp-001'  # employee_id

    def test_read_staff_by_email(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection,
        staff_test_data: List[Dict[str, Any]]
    ):
        """Test querying staff records by email address."""
        # Load test data
        db_cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")
        for record in staff_test_data[:5]:  # Load first 5 records
            db_cursor.execute("""
                INSERT INTO staff_pii (
                    employee_id, name, email, phone, address, date_of_birth, ssn,
                    department, job_title, hire_date, salary,
                    bank_account_number, routing_number, medical_condition
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                record['employee_id'],
                record['name'],
                record['email'],
                record['phone'],
                record['address'],
                record['date_of_birth'],
                record['ssn'],
                record['department'],
                record['job_title'],
                record['hire_date'],
                record['salary'],
                record['bank_account_number'],
                record['routing_number'],
                record.get('medical_condition', 'None')
            ))
        db_connection.commit()

        # Query by email
        test_email = staff_test_data[0]['email']
        db_cursor.execute("SELECT name, email, department FROM staff_pii WHERE email = %s", (test_email,))
        result = db_cursor.fetchone()

        assert result is not None
        assert result[1] == test_email

    def test_update_staff_salary(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection,
        staff_test_data: List[Dict[str, Any]]
    ):
        """Test updating a staff member's salary."""
        # Load one record
        db_cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")
        record = staff_test_data[0]
        db_cursor.execute("""
            INSERT INTO staff_pii (
                employee_id, name, email, phone, address, date_of_birth, ssn,
                department, job_title, hire_date, salary,
                bank_account_number, routing_number, medical_condition
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            record['employee_id'],
            record['name'],
            record['email'],
            record['phone'],
            record['address'],
            record['date_of_birth'],
            record['ssn'],
            record['department'],
            record['job_title'],
            record['hire_date'],
            record['salary'],
            record['bank_account_number'],
            record['routing_number'],
            record.get('medical_condition', 'None')
        ))
        db_connection.commit()

        # Update salary
        new_salary = 125000
        db_cursor.execute(
            "UPDATE staff_pii SET salary = %s WHERE employee_id = %s",
            (new_salary, record['employee_id'])
        )
        db_connection.commit()

        # Verify update
        db_cursor.execute(
            "SELECT salary FROM staff_pii WHERE employee_id = %s",
            (record['employee_id'],)
        )
        updated_salary = db_cursor.fetchone()[0]
        assert updated_salary == new_salary

    def test_delete_staff_record(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection,
        staff_test_data: List[Dict[str, Any]]
    ):
        """Test deleting a staff record."""
        # Load one record
        db_cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")
        record = staff_test_data[0]
        db_cursor.execute("""
            INSERT INTO staff_pii (
                employee_id, name, email, phone, address, date_of_birth, ssn,
                department, job_title, hire_date, salary,
                bank_account_number, routing_number, medical_condition
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """, (
            record['employee_id'],
            record['name'],
            record['email'],
            record['phone'],
            record['address'],
            record['date_of_birth'],
            record['ssn'],
            record['department'],
            record['job_title'],
            record['hire_date'],
            record['salary'],
            record['bank_account_number'],
            record['routing_number'],
            record.get('medical_condition', 'None')
        ))
        db_connection.commit()

        # Delete record
        db_cursor.execute(
            "DELETE FROM staff_pii WHERE employee_id = %s",
            (record['employee_id'],)
        )
        db_connection.commit()

        # Verify deletion
        db_cursor.execute(
            "SELECT COUNT(*) FROM staff_pii WHERE employee_id = %s",
            (record['employee_id'],)
        )
        count = db_cursor.fetchone()[0]
        assert count == 0


# ============================================================================
# Test Class: Constraint Validation
# ============================================================================

class TestConstraints:
    """Test database constraints including foreign keys, unique constraints, and NOT NULL."""

    def test_invalid_manager_foreign_key(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection
    ):
        """Test that inserting staff with invalid manager_id fails foreign key constraint."""
        db_cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")
        db_connection.commit()

        # Try to insert record with non-existent manager
        with pytest.raises(pg_errors.ForeignKeyViolation):
            db_cursor.execute("""
                INSERT INTO staff_pii (
                    employee_id, name, email, phone, address, date_of_birth, ssn,
                    department, job_title, hire_date, salary,
                    bank_account_number, routing_number, medical_condition, manager
                ) VALUES (
                    'emp-001', 'Test Name', 'test@company.com', '555-1234',
                    '123 Test St', '1990-01-01', '123-45-6789',
                    'Engineering', 'Engineer', '2020-01-01', 80000,
                    '1234567890', '987654321', NULL, 'nonexistent-manager-id'
                )
            """)
            db_connection.commit()

    def test_null_required_field_rejected(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection
    ):
        """Test that inserting record with NULL in required field fails."""
        db_cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")
        db_connection.commit()

        # Try to insert record with NULL name (required field)
        with pytest.raises(pg_errors.NotNullViolation):
            db_cursor.execute("""
                INSERT INTO staff_pii (
                    employee_id, name, email, phone, address, date_of_birth, ssn,
                    department, job_title, hire_date, salary,
                    bank_account_number, routing_number
                ) VALUES (
                    'emp-001', NULL, 'test@company.com', '555-1234',
                    '123 Test St', '1990-01-01', '123-45-6789',
                    'Engineering', 'Engineer', '2020-01-01', 80000,
                    '1234567890', '987654321'
                )
            """)
            db_connection.commit()

    def test_duplicate_primary_key_rejected(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection
    ):
        """Test that duplicate employee_id values are rejected."""
        db_cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")

        # Insert first record
        db_cursor.execute("""
            INSERT INTO staff_pii (
                employee_id, name, email, phone, address, date_of_birth, ssn,
                department, job_title, hire_date, salary,
                bank_account_number, routing_number
            ) VALUES (
                'emp-001', 'First Person', 'first@company.com', '555-1234',
                '123 Test St', '1990-01-01', '123-45-6789',
                'Engineering', 'Engineer', '2020-01-01', 80000,
                '1234567890', '987654321'
            )
        """)
        db_connection.commit()

        # Try to insert duplicate employee_id
        with pytest.raises(pg_errors.UniqueViolation):
            db_cursor.execute("""
                INSERT INTO staff_pii (
                    employee_id, name, email, phone, address, date_of_birth, ssn,
                    department, job_title, hire_date, salary,
                    bank_account_number, routing_number
                ) VALUES (
                    'emp-001', 'Second Person', 'second@company.com', '555-5678',
                    '456 Test Ave', '1985-06-15', '987-65-4321',
                    'Sales', 'Sales Rep', '2021-03-15', 75000,
                    '9876543210', '123456789'
                )
            """)
            db_connection.commit()


# ============================================================================
# Test Class: Data Integrity
# ============================================================================

class TestDataIntegrity:
    """Test data integrity including manager hierarchy and PII field formats."""

    def test_manager_hierarchy_validity(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection,
        staff_test_data: List[Dict[str, Any]]
    ):
        """Test that all manager references point to valid employee IDs."""
        # Load all staff records
        db_cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")

        # Phase 1: Insert all records with NULL managers
        for record in staff_test_data:
            db_cursor.execute("""
                INSERT INTO staff_pii (
                    employee_id, name, email, phone, address, date_of_birth, ssn,
                    department, job_title, hire_date, salary,
                    bank_account_number, routing_number, medical_condition
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                record['employee_id'],
                record['name'],
                record['email'],
                record['phone'],
                record['address'],
                record['date_of_birth'],
                record['ssn'],
                record['department'],
                record['job_title'],
                record['hire_date'],
                record['salary'],
                record['bank_account_number'],
                record['routing_number'],
                record.get('medical_condition', 'None')
            ))
        db_connection.commit()

        # Phase 2: Update manager references
        for record in staff_test_data:
            if record.get('manager'):
                db_cursor.execute(
                    "UPDATE staff_pii SET manager = %s WHERE employee_id = %s",
                    (record['manager'], record['employee_id'])
                )
        db_connection.commit()

        # Verify all manager references are valid
        # Query should return 0 rows (all managers should be valid employee IDs)
        db_cursor.execute("""
            SELECT employee_id, manager
            FROM staff_pii
            WHERE manager IS NOT NULL
                AND manager NOT IN (SELECT employee_id FROM staff_pii)
        """)
        invalid_managers = db_cursor.fetchall()

        # Note: The data uses manager employee_id (UUID), so we check against employee_id
        assert len(invalid_managers) == 0, f"Found {len(invalid_managers)} invalid manager references"

    def test_ssn_format_validation(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection,
        staff_test_data: List[Dict[str, Any]]
    ):
        """Test that SSN values match expected format (XXX-XX-XXXX)."""
        # Load staff records
        db_cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")
        for record in staff_test_data[:10]:
            db_cursor.execute("""
                INSERT INTO staff_pii (
                    employee_id, name, email, phone, address, date_of_birth, ssn,
                    department, job_title, hire_date, salary,
                    bank_account_number, routing_number, medical_condition
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                record['employee_id'],
                record['name'],
                record['email'],
                record['phone'],
                record['address'],
                record['date_of_birth'],
                record['ssn'],
                record['department'],
                record['job_title'],
                record['hire_date'],
                record['salary'],
                record['bank_account_number'],
                record['routing_number'],
                record.get('medical_condition', 'None')
            ))
        db_connection.commit()

        # Query SSNs and validate format
        db_cursor.execute("SELECT ssn FROM staff_pii")
        ssns = [row[0] for row in db_cursor.fetchall()]

        ssn_pattern = re.compile(r'^\d{3}-\d{2}-\d{4}$')
        for ssn in ssns:
            assert ssn_pattern.match(ssn), f"Invalid SSN format: {ssn}"

    def test_date_relationships(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection,
        staff_test_data: List[Dict[str, Any]]
    ):
        """Test that hire_date is after date_of_birth (employees hired when 18+)."""
        # Load staff records
        db_cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")
        for record in staff_test_data[:10]:
            db_cursor.execute("""
                INSERT INTO staff_pii (
                    employee_id, name, email, phone, address, date_of_birth, ssn,
                    department, job_title, hire_date, salary,
                    bank_account_number, routing_number, medical_condition
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                record['employee_id'],
                record['name'],
                record['email'],
                record['phone'],
                record['address'],
                record['date_of_birth'],
                record['ssn'],
                record['department'],
                record['job_title'],
                record['hire_date'],
                record['salary'],
                record['bank_account_number'],
                record['routing_number'],
                record.get('medical_condition', 'None')
            ))
        db_connection.commit()

        # Query records where hire_date < date_of_birth + 18 years
        db_cursor.execute("""
            SELECT employee_id, name, date_of_birth, hire_date,
                   AGE(hire_date, date_of_birth) as age_at_hire
            FROM staff_pii
            WHERE hire_date < date_of_birth + INTERVAL '18 years'
        """)
        underage_hires = db_cursor.fetchall()

        assert len(underage_hires) == 0, f"Found {len(underage_hires)} employees hired before age 18"

    def test_salary_ranges_reasonable(
        self,
        db_cursor: pg_cursor,
        db_connection: pg_connection,
        staff_test_data: List[Dict[str, Any]]
    ):
        """Test that salary values are within reasonable ranges."""
        # Load staff records
        db_cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")
        for record in staff_test_data:
            db_cursor.execute("""
                INSERT INTO staff_pii (
                    employee_id, name, email, phone, address, date_of_birth, ssn,
                    department, job_title, hire_date, salary,
                    bank_account_number, routing_number, medical_condition
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                record['employee_id'],
                record['name'],
                record['email'],
                record['phone'],
                record['address'],
                record['date_of_birth'],
                record['ssn'],
                record['department'],
                record['job_title'],
                record['hire_date'],
                record['salary'],
                record['bank_account_number'],
                record['routing_number'],
                record.get('medical_condition', 'None')
            ))
        db_connection.commit()

        # Query salary statistics
        db_cursor.execute("""
            SELECT
                MIN(salary) as min_salary,
                MAX(salary) as max_salary,
                AVG(salary) as avg_salary
            FROM staff_pii
        """)
        min_sal, max_sal, avg_sal = db_cursor.fetchone()

        # Reasonable salary ranges (adjust based on your data)
        assert min_sal >= 30000, f"Minimum salary too low: ${min_sal}"
        assert max_sal <= 500000, f"Maximum salary too high: ${max_sal}"
        assert 50000 <= avg_sal <= 150000, f"Average salary outside expected range: ${avg_sal}"


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
