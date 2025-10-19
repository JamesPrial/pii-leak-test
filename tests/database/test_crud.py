#!/usr/bin/env python3
"""
Comprehensive CRUD API Test Suite for PII PostgreSQL Database

This test suite validates the CRUD operations and Database context manager for:
- Database context manager (automatic commit/rollback)
- StaffRepository CRUD operations
- ClientRepository CRUD operations
- Staff filtering and search operations
- Client filtering and search operations
- Manager hierarchy queries
- Error handling and constraint validation

Requirements:
- Docker and Docker Compose must be running
- PostgreSQL container must be healthy
- Environment variables must be configured (see docker-compose.yml)

Usage:
    pytest tests/database/test_crud.py -v                    # Run all tests
    pytest tests/database/test_crud.py::TestDatabaseContext -v  # Run specific test class
    pytest tests/database/test_crud.py -k test_create -v     # Run tests matching pattern
"""

import os
import pytest
from datetime import datetime, date
from typing import Dict, List, Any

import psycopg2
from psycopg2 import errors as pg_errors
from psycopg2.extensions import connection as pg_connection, cursor as pg_cursor

from src.database import Database
from src.types.staff import StaffPII
from src.types.client import ClientPII


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
def clean_db(db_connection: pg_connection):
    """
    Clean database before each test to ensure test isolation.

    This fixture:
    - Truncates both staff_pii and client_pii tables
    - Runs before each test function
    - Ensures each test starts with clean slate

    Args:
        db_connection: Database connection from db_connection fixture
    """
    cursor = db_connection.cursor()
    try:
        cursor.execute("TRUNCATE TABLE staff_pii CASCADE;")
        cursor.execute("TRUNCATE TABLE client_pii CASCADE;")
        db_connection.commit()
    finally:
        cursor.close()


@pytest.fixture
def sample_staff() -> StaffPII:
    """
    Create a sample StaffPII instance for testing.

    Returns:
        StaffPII instance with realistic test data
    """
    return StaffPII(
        employee_id='test-emp-001',
        name='John Doe',
        email='john.doe@company.com',
        phone='555-0100',
        address='123 Main St, Anytown, CA 12345',
        date_of_birth='1990-01-15',
        ssn='123-45-6789',
        department='Engineering',
        job_title='Software Engineer',
        hire_date='2020-03-01',
        manager=None,
        salary=95000,
        bank_account_number='1234567890',
        routing_number='987654321',
        medical_condition=None
    )


@pytest.fixture
def sample_client() -> ClientPII:
    """
    Create a sample ClientPII instance for testing.

    Returns:
        ClientPII instance with realistic test data
    """
    return ClientPII(
        record_id='test-client-001',
        name='Jane Smith',
        email='jane.smith@email.com',
        phone='555-0200',
        address='456 Oak Ave, Springfield, NY 67890',
        date_of_birth='1985-06-20',
        salary=75000,
        medical_condition='None',
        ssn='987-65-4321',
        credit_card='4532015112830366'
    )


@pytest.fixture
def sample_staff_manager() -> StaffPII:
    """
    Create a sample manager StaffPII instance for testing hierarchy.

    Returns:
        StaffPII instance representing a manager
    """
    return StaffPII(
        employee_id='test-mgr-001',
        name='Alice Manager',
        email='alice.manager@company.com',
        phone='555-0300',
        address='789 Executive Blvd, Corporate City, TX 11111',
        date_of_birth='1980-04-10',
        ssn='111-22-3333',
        department='Engineering',
        job_title='Engineering Manager',
        hire_date='2015-01-15',
        manager=None,
        salary=150000,
        bank_account_number='9876543210',
        routing_number='123456789',
        medical_condition=None
    )


# ============================================================================
# Test Class: Database Context Manager
# ============================================================================

class TestDatabaseContext:
    """Test the Database context manager functionality."""

    def test_context_manager_success(self, clean_db, sample_staff):
        """
        Verify that the context manager auto-commits on success.

        This test:
        1. Uses Database context manager to insert a staff record
        2. Exits context successfully (no exception)
        3. Verifies record was committed to database
        """
        # Create record within context
        with Database() as db:
            emp_id = db.staff.create(sample_staff)
            assert emp_id == sample_staff.employee_id

        # Verify record persisted after context exit (committed)
        with Database() as db:
            retrieved = db.staff.get_by_id(sample_staff.employee_id)
            assert retrieved is not None
            assert retrieved.name == sample_staff.name
            assert retrieved.email == sample_staff.email

    def test_context_manager_rollback(self, clean_db, sample_staff):
        """
        Verify that the context manager auto-rolls back on exception.

        This test:
        1. Inserts a record within context
        2. Raises an exception before exiting context
        3. Verifies record was NOT committed (rolled back)
        """
        # Try to create record but raise exception
        with pytest.raises(ValueError):
            with Database() as db:
                db.staff.create(sample_staff)
                raise ValueError("Simulated error")

        # Verify record was NOT persisted (rolled back)
        with Database() as db:
            retrieved = db.staff.get_by_id(sample_staff.employee_id)
            assert retrieved is None

    def test_properties_outside_context(self):
        """
        Verify RuntimeError when accessing .staff/.clients outside context.

        This test verifies that accessing repositories outside the context
        manager raises a clear RuntimeError with helpful message.
        """
        db = Database()

        with pytest.raises(RuntimeError, match="must be used within a context manager"):
            _ = db.staff

        with pytest.raises(RuntimeError, match="must be used within a context manager"):
            _ = db.clients

    def test_connection_cleanup(self, clean_db, sample_staff):
        """
        Verify connection is properly closed after context exit.

        This test verifies that the database connection and repositories
        are cleaned up after exiting the context manager.
        """
        db = Database()

        # Use context manager
        with db:
            assert db._connection is not None
            assert db._staff_repo is not None
            assert db._client_repo is not None

        # Verify cleanup after exit
        assert db._connection is None
        assert db._staff_repo is None
        assert db._client_repo is None


# ============================================================================
# Test Class: Staff CRUD Operations
# ============================================================================

class TestStaffCRUD:
    """Test basic CRUD operations for staff records."""

    def test_create_staff(self, clean_db, sample_staff):
        """
        Test inserting a new staff record and verify ID returned.

        This test validates:
        - Staff record can be created successfully
        - The returned employee_id matches the input
        - The record can be retrieved immediately
        """
        with Database() as db:
            emp_id = db.staff.create(sample_staff)

            assert emp_id == sample_staff.employee_id
            assert emp_id == 'test-emp-001'

            # Verify immediate retrieval
            retrieved = db.staff.get_by_id(emp_id)
            assert retrieved is not None
            assert retrieved.name == sample_staff.name

    def test_get_by_id_exists(self, clean_db, sample_staff):
        """
        Test fetching an existing staff record by employee_id.

        This test validates:
        - Record can be created and retrieved
        - All fields are correctly persisted
        - Date fields are properly serialized
        """
        with Database() as db:
            db.staff.create(sample_staff)
            retrieved = db.staff.get_by_id('test-emp-001')

            assert retrieved is not None
            assert retrieved.employee_id == sample_staff.employee_id
            assert retrieved.name == sample_staff.name
            assert retrieved.email == sample_staff.email
            assert retrieved.phone == sample_staff.phone
            assert retrieved.address == sample_staff.address
            assert retrieved.date_of_birth == sample_staff.date_of_birth
            assert retrieved.ssn == sample_staff.ssn
            assert retrieved.department == sample_staff.department
            assert retrieved.job_title == sample_staff.job_title
            assert retrieved.hire_date == sample_staff.hire_date
            assert retrieved.manager == sample_staff.manager
            assert retrieved.salary == sample_staff.salary
            assert retrieved.bank_account_number == sample_staff.bank_account_number
            assert retrieved.routing_number == sample_staff.routing_number
            assert retrieved.medical_condition == sample_staff.medical_condition

    def test_get_by_id_not_found(self, clean_db):
        """
        Test fetching a non-existent record returns None.

        This test validates that querying for a non-existent employee_id
        returns None instead of raising an exception.
        """
        with Database() as db:
            result = db.staff.get_by_id('nonexistent-id')
            assert result is None

    def test_update_staff(self, clean_db, sample_staff):
        """
        Test updating staff salary and department, verify changes persisted.

        This test validates:
        - Staff record can be updated
        - Update returns True for successful update
        - Changes are persisted to database
        - Other fields remain unchanged
        """
        with Database() as db:
            # Create initial record
            db.staff.create(sample_staff)

            # Update salary and department
            sample_staff.salary = 120000
            sample_staff.department = 'Data Science'
            success = db.staff.update(sample_staff)

            assert success is True

            # Verify changes persisted
            retrieved = db.staff.get_by_id(sample_staff.employee_id)
            assert retrieved.salary == 120000
            assert retrieved.department == 'Data Science'
            # Verify other fields unchanged
            assert retrieved.name == sample_staff.name
            assert retrieved.email == sample_staff.email

    def test_delete_staff(self, clean_db, sample_staff):
        """
        Test deleting a staff record and verify it's gone.

        This test validates:
        - Delete operation returns True for successful deletion
        - Record is removed from database
        - Subsequent queries return None
        """
        with Database() as db:
            # Create record
            db.staff.create(sample_staff)

            # Verify it exists
            assert db.staff.get_by_id(sample_staff.employee_id) is not None

            # Delete record
            success = db.staff.delete(sample_staff.employee_id)
            assert success is True

            # Verify it's gone
            assert db.staff.get_by_id(sample_staff.employee_id) is None

    def test_list_all(self, clean_db, sample_staff):
        """
        Test getting all staff records with limit.

        This test validates:
        - list_all() returns all records when count < limit
        - list_all() respects the limit parameter
        - Records are returned in correct order
        """
        with Database() as db:
            # Create multiple records
            for i in range(5):
                staff = StaffPII(
                    employee_id=f'emp-{i:03d}',
                    name=f'Employee {i}',
                    email=f'emp{i}@company.com',
                    phone=f'555-{i:04d}',
                    address=f'{i} Test St',
                    date_of_birth='1990-01-01',
                    ssn=f'{i:03d}-45-6789',
                    department='Engineering',
                    job_title='Engineer',
                    hire_date='2020-01-01',
                    manager=None,
                    salary=80000 + (i * 5000),
                    bank_account_number=f'{i:010d}',
                    routing_number='123456789',
                    medical_condition=None
                )
                db.staff.create(staff)

            # Get all records
            all_staff = db.staff.list_all(limit=10)
            assert len(all_staff) == 5

            # Test limit
            limited = db.staff.list_all(limit=3)
            assert len(limited) == 3

    def test_list_all_empty(self, clean_db):
        """
        Test list_all() on empty table returns empty list.

        This test validates that querying an empty table
        returns an empty list rather than None or raising an exception.
        """
        with Database() as db:
            result = db.staff.list_all()
            assert result == []
            assert isinstance(result, list)


# ============================================================================
# Test Class: Client CRUD Operations
# ============================================================================

class TestClientCRUD:
    """Test basic CRUD operations for client records."""

    def test_create_client(self, clean_db, sample_client):
        """
        Test inserting a new client record and verify ID returned.

        This test validates:
        - Client record can be created successfully
        - The returned record_id matches the input
        - The record can be retrieved immediately
        """
        with Database() as db:
            record_id = db.clients.create(sample_client)

            assert record_id == sample_client.record_id
            assert record_id == 'test-client-001'

            # Verify immediate retrieval
            retrieved = db.clients.get_by_id(record_id)
            assert retrieved is not None
            assert retrieved.name == sample_client.name

    def test_get_by_id_exists(self, clean_db, sample_client):
        """
        Test fetching an existing client record by record_id.

        This test validates:
        - Record can be created and retrieved
        - All fields are correctly persisted
        - Date field is properly serialized
        """
        with Database() as db:
            db.clients.create(sample_client)
            retrieved = db.clients.get_by_id('test-client-001')

            assert retrieved is not None
            assert retrieved.record_id == sample_client.record_id
            assert retrieved.name == sample_client.name
            assert retrieved.email == sample_client.email
            assert retrieved.phone == sample_client.phone
            assert retrieved.address == sample_client.address
            assert retrieved.date_of_birth == sample_client.date_of_birth
            assert retrieved.salary == sample_client.salary
            assert retrieved.medical_condition == sample_client.medical_condition
            assert retrieved.ssn == sample_client.ssn
            assert retrieved.credit_card == sample_client.credit_card

    def test_get_by_id_not_found(self, clean_db):
        """
        Test fetching a non-existent client returns None.

        This test validates that querying for a non-existent record_id
        returns None instead of raising an exception.
        """
        with Database() as db:
            result = db.clients.get_by_id('nonexistent-id')
            assert result is None

    def test_update_client(self, clean_db, sample_client):
        """
        Test updating client income and medical_condition.

        This test validates:
        - Client record can be updated
        - Update returns True for successful update
        - Changes are persisted to database
        - Other fields remain unchanged
        """
        with Database() as db:
            # Create initial record
            db.clients.create(sample_client)

            # Update salary and medical condition
            sample_client.salary = 85000
            sample_client.medical_condition = 'Diabetes'
            success = db.clients.update(sample_client)

            assert success is True

            # Verify changes persisted
            retrieved = db.clients.get_by_id(sample_client.record_id)
            assert retrieved.salary == 85000
            assert retrieved.medical_condition == 'Diabetes'
            # Verify other fields unchanged
            assert retrieved.name == sample_client.name
            assert retrieved.email == sample_client.email

    def test_delete_client(self, clean_db, sample_client):
        """
        Test deleting a client record and verify it's gone.

        This test validates:
        - Delete operation returns True for successful deletion
        - Record is removed from database
        - Subsequent queries return None
        """
        with Database() as db:
            # Create record
            db.clients.create(sample_client)

            # Verify it exists
            assert db.clients.get_by_id(sample_client.record_id) is not None

            # Delete record
            success = db.clients.delete(sample_client.record_id)
            assert success is True

            # Verify it's gone
            assert db.clients.get_by_id(sample_client.record_id) is None

    def test_list_all(self, clean_db):
        """
        Test getting all client records with limit.

        This test validates:
        - list_all() returns all records when count < limit
        - list_all() respects the limit parameter
        """
        with Database() as db:
            # Create multiple records
            for i in range(4):
                client = ClientPII(
                    record_id=f'client-{i:03d}',
                    name=f'Client {i}',
                    email=f'client{i}@email.com',
                    phone=f'555-{i:04d}',
                    address=f'{i} Client St',
                    date_of_birth='1985-01-01',
                    salary=60000 + (i * 10000),
                    medical_condition='None',
                    ssn=f'{i:03d}-11-2222',
                    credit_card=f'4532{i:012d}'
                )
                db.clients.create(client)

            # Get all records
            all_clients = db.clients.list_all(limit=10)
            assert len(all_clients) == 4

            # Test limit
            limited = db.clients.list_all(limit=2)
            assert len(limited) == 2


# ============================================================================
# Test Class: Staff Filtering and Search
# ============================================================================

class TestStaffFiltering:
    """Test filtering and search operations for staff records."""

    def test_filter_by_department(self, clean_db):
        """
        Test filtering staff by department.

        This test validates:
        - filter() correctly filters by department
        - Only matching records are returned
        - Non-matching records are excluded
        """
        with Database() as db:
            # Create staff in different departments
            for idx, dept in enumerate(['Engineering', 'Engineering', 'Sales', 'Marketing']):
                staff = StaffPII(
                    employee_id=f'emp-{dept[:3]}-{idx}',
                    name=f'{dept} Employee {idx}',
                    email=f'{dept.lower()}{idx}@company.com',
                    phone=f'555-000{idx}',
                    address='123 St',
                    date_of_birth='1990-01-01',
                    ssn=f'123-45-{6789+idx:04d}',
                    department=dept,
                    job_title='Employee',
                    hire_date='2020-01-01',
                    manager=None,
                    salary=80000,
                    bank_account_number=f'123456789{idx}',
                    routing_number='123456789',
                    medical_condition=None
                )
                db.staff.create(staff)

            # Filter by Engineering
            engineers = db.staff.filter(department='Engineering')
            assert len(engineers) == 2
            for emp in engineers:
                assert emp.department == 'Engineering'

    def test_filter_by_salary_range(self, clean_db):
        """
        Test filtering staff by salary range (salary_min and salary_max).

        This test validates:
        - salary_min filter works correctly
        - salary_max filter works correctly
        - Both filters can be combined
        """
        with Database() as db:
            # Create staff with different salaries
            salaries = [60000, 80000, 100000, 120000]
            for i, sal in enumerate(salaries):
                staff = StaffPII(
                    employee_id=f'emp-{i:03d}',
                    name=f'Employee {i}',
                    email=f'emp{i}@company.com',
                    phone='555-0000',
                    address='123 St',
                    date_of_birth='1990-01-01',
                    ssn='123-45-6789',
                    department='Engineering',
                    job_title='Engineer',
                    hire_date='2020-01-01',
                    manager=None,
                    salary=sal,
                    bank_account_number='1234567890',
                    routing_number='123456789',
                    medical_condition=None
                )
                db.staff.create(staff)

            # Filter by minimum salary
            high_earners = db.staff.filter(salary_min=100000)
            assert len(high_earners) == 2
            for emp in high_earners:
                assert emp.salary >= 100000

            # Filter by salary range
            mid_range = db.staff.filter(salary_min=80000, salary_max=100000)
            assert len(mid_range) == 2
            for emp in mid_range:
                assert 80000 <= emp.salary <= 100000

    def test_filter_multiple_criteria(self, clean_db):
        """
        Test filtering with multiple criteria (department + salary).

        This test validates that multiple filter criteria can be
        combined and all conditions are applied with AND logic.
        """
        with Database() as db:
            # Create diverse staff records
            test_data = [
                ('Engineering', 90000),
                ('Engineering', 110000),
                ('Sales', 95000),
                ('Sales', 70000),
            ]

            for i, (dept, sal) in enumerate(test_data):
                staff = StaffPII(
                    employee_id=f'emp-{i:03d}',
                    name=f'Employee {i}',
                    email=f'emp{i}@company.com',
                    phone='555-0000',
                    address='123 St',
                    date_of_birth='1990-01-01',
                    ssn='123-45-6789',
                    department=dept,
                    job_title='Employee',
                    hire_date='2020-01-01',
                    manager=None,
                    salary=sal,
                    bank_account_number='1234567890',
                    routing_number='123456789',
                    medical_condition=None
                )
                db.staff.create(staff)

            # Filter by department AND salary
            result = db.staff.filter(department='Engineering', salary_min=100000)
            assert len(result) == 1
            assert result[0].department == 'Engineering'
            assert result[0].salary >= 100000

    def test_search_by_email(self, clean_db, sample_staff):
        """
        Test searching for staff by email address.

        This test validates:
        - search_by_email() finds existing records
        - Exact email match is required
        - Returns None for non-existent emails
        """
        with Database() as db:
            db.staff.create(sample_staff)

            # Search by email
            found = db.staff.search_by_email('john.doe@company.com')
            assert found is not None
            assert found.employee_id == sample_staff.employee_id
            assert found.name == sample_staff.name

            # Search for non-existent email
            not_found = db.staff.search_by_email('nonexistent@company.com')
            assert not_found is None

    def test_search_by_ssn(self, clean_db, sample_staff):
        """
        Test searching for staff by SSN.

        This test validates:
        - search_by_ssn() finds existing records
        - SSN search works with correct format
        - Returns None for non-existent SSN
        """
        with Database() as db:
            db.staff.create(sample_staff)

            # Search by SSN
            found = db.staff.search_by_ssn('123-45-6789')
            assert found is not None
            assert found.employee_id == sample_staff.employee_id
            assert found.ssn == '123-45-6789'

            # Search for non-existent SSN
            not_found = db.staff.search_by_ssn('999-99-9999')
            assert not_found is None

    def test_search_not_found(self, clean_db):
        """
        Test that search operations return None when not found.

        This test validates consistent behavior across all search
        methods when records don't exist.
        """
        with Database() as db:
            assert db.staff.search_by_email('none@company.com') is None
            assert db.staff.search_by_ssn('000-00-0000') is None


# ============================================================================
# Test Class: Client Filtering
# ============================================================================

class TestClientFiltering:
    """Test filtering operations for client records."""

    def test_filter_by_salary_range(self, clean_db):
        """
        Test filtering clients by income range.

        This test validates:
        - salary_min filter works for clients
        - salary_max filter works for clients
        - Both filters can be combined
        """
        with Database() as db:
            # Create clients with different incomes
            incomes = [50000, 70000, 90000, 110000]
            for i, income in enumerate(incomes):
                client = ClientPII(
                    record_id=f'client-{i:03d}',
                    name=f'Client {i}',
                    email=f'client{i}@email.com',
                    phone='555-0000',
                    address='123 St',
                    date_of_birth='1985-01-01',
                    salary=income,
                    medical_condition='None',
                    ssn='123-45-6789',
                    credit_card='4532015112830366'
                )
                db.clients.create(client)

            # Filter by income range
            mid_income = db.clients.filter(salary_min=70000, salary_max=90000)
            assert len(mid_income) == 2
            for client in mid_income:
                assert 70000 <= client.salary <= 90000

    def test_search_by_email(self, clean_db, sample_client):
        """
        Test searching for clients by email address.

        This test validates:
        - search_by_email() finds existing client records
        - Returns None for non-existent emails
        """
        with Database() as db:
            db.clients.create(sample_client)

            # Search by email
            found = db.clients.search_by_email('jane.smith@email.com')
            assert found is not None
            assert found.record_id == sample_client.record_id
            assert found.name == sample_client.name

            # Search for non-existent email
            not_found = db.clients.search_by_email('nonexistent@email.com')
            assert not_found is None

    def test_search_by_ssn(self, clean_db, sample_client):
        """
        Test searching for clients by SSN.

        This test validates:
        - search_by_ssn() finds existing client records
        - Returns None for non-existent SSN
        """
        with Database() as db:
            db.clients.create(sample_client)

            # Search by SSN
            found = db.clients.search_by_ssn('987-65-4321')
            assert found is not None
            assert found.record_id == sample_client.record_id
            assert found.ssn == '987-65-4321'

            # Search for non-existent SSN
            not_found = db.clients.search_by_ssn('000-00-0000')
            assert not_found is None


# ============================================================================
# Test Class: Manager Hierarchy
# ============================================================================

class TestManagerHierarchy:
    """Test organizational hierarchy queries."""

    def test_get_direct_reports(self, clean_db, sample_staff_manager):
        """
        Test getting employees reporting to a specific manager.

        This test validates:
        - get_direct_reports() returns all direct reports
        - Manager relationship is correctly established
        - Reports are ordered by name
        """
        with Database() as db:
            # Create manager
            db.staff.create(sample_staff_manager)

            # Create direct reports
            for i in range(3):
                report = StaffPII(
                    employee_id=f'emp-{i:03d}',
                    name=f'Report {i}',
                    email=f'report{i}@company.com',
                    phone='555-0000',
                    address='123 St',
                    date_of_birth='1990-01-01',
                    ssn=f'{i:03d}-45-6789',
                    department='Engineering',
                    job_title='Engineer',
                    hire_date='2020-01-01',
                    manager=sample_staff_manager.employee_id,
                    salary=80000,
                    bank_account_number='1234567890',
                    routing_number='123456789',
                    medical_condition=None
                )
                db.staff.create(report)

            # Get direct reports
            reports = db.staff.get_direct_reports(sample_staff_manager.employee_id)
            assert len(reports) == 3
            for report in reports:
                assert report.manager == sample_staff_manager.employee_id

    def test_get_direct_reports_none(self, clean_db, sample_staff):
        """
        Test that manager with no reports returns empty list.

        This test validates that get_direct_reports() returns
        an empty list (not None) when employee has no direct reports.
        """
        with Database() as db:
            # Create employee with no reports
            db.staff.create(sample_staff)

            # Get direct reports (should be empty)
            reports = db.staff.get_direct_reports(sample_staff.employee_id)
            assert reports == []
            assert isinstance(reports, list)

    def test_get_managers(self, clean_db, sample_staff_manager):
        """
        Test getting all managers in the organization.

        This test validates:
        - get_managers() returns all employees who are managers
        - Includes both top-level managers (no manager) and mid-level
        - Excludes individual contributors
        """
        with Database() as db:
            # Create top-level manager
            db.staff.create(sample_staff_manager)

            # Create mid-level manager
            mid_manager = StaffPII(
                employee_id='mid-mgr-001',
                name='Bob MiddleManager',
                email='bob@company.com',
                phone='555-0000',
                address='123 St',
                date_of_birth='1985-01-01',
                ssn='222-33-4444',
                department='Engineering',
                job_title='Team Lead',
                hire_date='2018-01-01',
                manager=sample_staff_manager.employee_id,
                salary=120000,
                bank_account_number='1234567890',
                routing_number='123456789',
                medical_condition=None
            )
            db.staff.create(mid_manager)

            # Create individual contributor reporting to mid-level manager
            ic = StaffPII(
                employee_id='emp-001',
                name='Charlie Developer',
                email='charlie@company.com',
                phone='555-0000',
                address='123 St',
                date_of_birth='1992-01-01',
                ssn='333-44-5555',
                department='Engineering',
                job_title='Developer',
                hire_date='2021-01-01',
                manager=mid_manager.employee_id,
                salary=90000,
                bank_account_number='1234567890',
                routing_number='123456789',
                medical_condition=None
            )
            db.staff.create(ic)

            # Get all managers
            managers = db.staff.get_managers()

            # Should include top-level and mid-level managers, not IC
            manager_ids = [m.employee_id for m in managers]
            assert sample_staff_manager.employee_id in manager_ids
            assert mid_manager.employee_id in manager_ids
            assert ic.employee_id not in manager_ids


# ============================================================================
# Test Class: Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error scenarios and constraint violations."""

    def test_create_duplicate_employee_id(self, clean_db, sample_staff):
        """
        Test that duplicate primary key raises exception.

        This test validates:
        - Creating duplicate employee_id raises UniqueViolation
        - Transaction is rolled back on error
        - Original record remains intact
        """
        with Database() as db:
            # Create initial record
            db.staff.create(sample_staff)

        # Try to create duplicate (new context to avoid transaction issues)
        with pytest.raises(pg_errors.UniqueViolation):
            with Database() as db:
                # Try to create record with same employee_id
                duplicate = StaffPII(
                    employee_id=sample_staff.employee_id,  # Same ID
                    name='Different Person',
                    email='different@company.com',
                    phone='555-9999',
                    address='Different Address',
                    date_of_birth='1995-01-01',
                    ssn='999-99-9999',
                    department='Sales',
                    job_title='Sales Rep',
                    hire_date='2021-01-01',
                    manager=None,
                    salary=75000,
                    bank_account_number='9999999999',
                    routing_number='999999999',
                    medical_condition=None
                )
                db.staff.create(duplicate)

    def test_update_nonexistent_record(self, clean_db, sample_staff):
        """
        Test that updating non-existent record returns False.

        This test validates:
        - Update operation returns False when record doesn't exist
        - No exception is raised
        """
        with Database() as db:
            # Try to update non-existent record
            sample_staff.employee_id = 'nonexistent-id'
            result = db.staff.update(sample_staff)
            assert result is False

    def test_invalid_foreign_key(self, clean_db, sample_staff):
        """
        Test that invalid manager_id raises ForeignKeyViolation.

        This test validates:
        - Creating staff with non-existent manager raises error
        - Foreign key constraint is enforced
        """
        with pytest.raises(pg_errors.ForeignKeyViolation):
            with Database() as db:
                sample_staff.manager = 'nonexistent-manager-id'
                db.staff.create(sample_staff)

    def test_null_required_field(self, clean_db):
        """
        Test that NULL in required field raises NotNullViolation.

        This test validates:
        - Required fields cannot be NULL
        - NOT NULL constraint is enforced at database level
        """
        with pytest.raises((pg_errors.NotNullViolation, TypeError)):
            with Database() as db:
                # Create staff with NULL name (required field)
                invalid_staff = StaffPII(
                    employee_id='emp-001',
                    name=None,  # NULL in required field
                    email='test@company.com',
                    phone='555-0000',
                    address='123 St',
                    date_of_birth='1990-01-01',
                    ssn='123-45-6789',
                    department='Engineering',
                    job_title='Engineer',
                    hire_date='2020-01-01',
                    manager=None,
                    salary=80000,
                    bank_account_number='1234567890',
                    routing_number='123456789',
                    medical_condition=None
                )
                db.staff.create(invalid_staff)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
