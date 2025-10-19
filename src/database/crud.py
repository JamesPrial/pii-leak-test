"""
CRUD Repository Classes for Staff and Client PII Records

This module provides repository pattern implementations for managing
StaffPII and ClientPII records in PostgreSQL. Both repositories:
- Accept a psycopg2 cursor for database operations
- Convert database rows to/from dataclass instances
- Use parameterized queries to prevent SQL injection
- Handle NULL values appropriately

Usage:
    import psycopg2
    from src.types.staff import StaffPII
    from src.types.client import ClientPII
    from src.database.crud import StaffRepository, ClientRepository

    conn = psycopg2.connect(...)
    cursor = conn.cursor()

    staff_repo = StaffRepository(cursor)
    employee_id = staff_repo.create(staff_record)
    staff = staff_repo.get_by_id(employee_id)

    client_repo = ClientRepository(cursor)
    record_id = client_repo.create(client_record)
    client = client_repo.get_by_id(record_id)
"""

from typing import List, Optional, Any
from datetime import date

from src.types.staff import StaffPII
from src.types.client import ClientPII


class StaffRepository:
    """
    Repository for managing StaffPII records in the staff_pii table.

    Provides CRUD operations and specialized queries for employee data,
    including manager relationships and organizational hierarchy.
    """

    def __init__(self, cursor):
        """
        Initialize repository with database cursor.

        Args:
            cursor: psycopg2 cursor for executing database operations
        """
        self.cursor = cursor

    def _row_to_staff(self, row: tuple) -> StaffPII:
        """
        Convert database row tuple to StaffPII dataclass instance.

        Args:
            row: Database row tuple in column order matching staff_pii table schema

        Returns:
            StaffPII instance with data from the row

        Note:
            Date fields (date_of_birth, hire_date) are converted from date objects
            to ISO format strings to match dataclass expectations.
        """
        return StaffPII(
            employee_id=row[0],
            name=row[1],
            email=row[2],
            phone=row[3],
            address=row[4],
            date_of_birth=row[5].isoformat() if isinstance(row[5], date) else row[5],
            ssn=row[6],
            department=row[7],
            job_title=row[8],
            hire_date=row[9].isoformat() if isinstance(row[9], date) else row[9],
            manager=row[10],  # May be None
            salary=row[11],
            bank_account_number=row[12],
            routing_number=row[13],
            medical_condition=row[14]  # May be None
        )

    def create(self, staff: StaffPII) -> str:
        """
        Insert a new staff record into the database.

        Args:
            staff: StaffPII instance to insert

        Returns:
            The employee_id of the inserted record

        Raises:
            psycopg2.IntegrityError: If employee_id already exists or constraint violated
        """
        query = """
            INSERT INTO staff_pii (
                employee_id, name, email, phone, address, date_of_birth, ssn,
                department, job_title, hire_date, manager, salary,
                bank_account_number, routing_number, medical_condition
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        self.cursor.execute(query, (
            staff.employee_id,
            staff.name,
            staff.email,
            staff.phone,
            staff.address,
            staff.date_of_birth,
            staff.ssn,
            staff.department,
            staff.job_title,
            staff.hire_date,
            staff.manager,
            staff.salary,
            staff.bank_account_number,
            staff.routing_number,
            staff.medical_condition
        ))
        return staff.employee_id

    def get_by_id(self, employee_id: str) -> Optional[StaffPII]:
        """
        Fetch a staff record by employee ID.

        Args:
            employee_id: The employee ID to search for

        Returns:
            StaffPII instance if found, None otherwise
        """
        query = """
            SELECT employee_id, name, email, phone, address, date_of_birth, ssn,
                   department, job_title, hire_date, manager, salary,
                   bank_account_number, routing_number, medical_condition
            FROM staff_pii
            WHERE employee_id = %s
        """
        self.cursor.execute(query, (employee_id,))
        row = self.cursor.fetchone()
        return self._row_to_staff(row) if row else None

    def update(self, staff: StaffPII) -> bool:
        """
        Update an existing staff record.

        Args:
            staff: StaffPII instance with updated data (employee_id must exist)

        Returns:
            True if record was updated, False if employee_id not found
        """
        query = """
            UPDATE staff_pii
            SET name = %s, email = %s, phone = %s, address = %s,
                date_of_birth = %s, ssn = %s, department = %s, job_title = %s,
                hire_date = %s, manager = %s, salary = %s,
                bank_account_number = %s, routing_number = %s,
                medical_condition = %s
            WHERE employee_id = %s
        """
        self.cursor.execute(query, (
            staff.name,
            staff.email,
            staff.phone,
            staff.address,
            staff.date_of_birth,
            staff.ssn,
            staff.department,
            staff.job_title,
            staff.hire_date,
            staff.manager,
            staff.salary,
            staff.bank_account_number,
            staff.routing_number,
            staff.medical_condition,
            staff.employee_id
        ))
        return self.cursor.rowcount > 0

    def delete(self, employee_id: str) -> bool:
        """
        Delete a staff record by employee ID.

        Args:
            employee_id: The employee ID to delete

        Returns:
            True if record was deleted, False if employee_id not found

        Note:
            May fail if employee is referenced as a manager by other records
            due to foreign key constraint.
        """
        query = "DELETE FROM staff_pii WHERE employee_id = %s"
        self.cursor.execute(query, (employee_id,))
        return self.cursor.rowcount > 0

    def list_all(self, limit: int = 100) -> List[StaffPII]:
        """
        Retrieve all staff records with optional limit.

        Args:
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of StaffPII instances
        """
        query = """
            SELECT employee_id, name, email, phone, address, date_of_birth, ssn,
                   department, job_title, hire_date, manager, salary,
                   bank_account_number, routing_number, medical_condition
            FROM staff_pii
            ORDER BY employee_id
            LIMIT %s
        """
        self.cursor.execute(query, (limit,))
        return [self._row_to_staff(row) for row in self.cursor.fetchall()]

    def get_all(self, limit: Optional[int] = None) -> List[StaffPII]:
        """
        Retrieve all staff records with optional limit.

        Args:
            limit: Maximum number of records to return (default: None, returns all)

        Returns:
            List of StaffPII instances
        """
        if limit is None:
            query = """
                SELECT employee_id, name, email, phone, address, date_of_birth, ssn,
                       department, job_title, hire_date, manager, salary,
                       bank_account_number, routing_number, medical_condition
                FROM staff_pii
                ORDER BY employee_id
            """
            self.cursor.execute(query)
        else:
            query = """
                SELECT employee_id, name, email, phone, address, date_of_birth, ssn,
                       department, job_title, hire_date, manager, salary,
                       bank_account_number, routing_number, medical_condition
                FROM staff_pii
                ORDER BY employee_id
                LIMIT %s
            """
            self.cursor.execute(query, (limit,))
        return [self._row_to_staff(row) for row in self.cursor.fetchall()]

    def filter(self, **kwargs) -> List[StaffPII]:
        """
        Filter staff records by specified field criteria.

        Supported filters:
            - department: Exact match on department name
            - salary_min: Salary >= specified value
            - salary_max: Salary <= specified value
            - job_title: Exact match on job title
            - manager: Exact match on manager employee_id (or None for no manager)

        Args:
            **kwargs: Field filters (e.g., department='Engineering', salary_min=80000)

        Returns:
            List of StaffPII instances matching all specified criteria

        Examples:
            # Engineering employees
            staff_repo.filter(department='Engineering')

            # Salary range
            staff_repo.filter(salary_min=80000, salary_max=120000)

            # Top-level managers (no manager)
            staff_repo.filter(manager=None)

            # Combined filters
            staff_repo.filter(department='Sales', salary_min=100000)
        """
        conditions = []
        params = []

        if 'department' in kwargs:
            conditions.append("department = %s")
            params.append(kwargs['department'])

        if 'salary_min' in kwargs:
            conditions.append("salary >= %s")
            params.append(kwargs['salary_min'])

        if 'salary_max' in kwargs:
            conditions.append("salary <= %s")
            params.append(kwargs['salary_max'])

        if 'job_title' in kwargs:
            conditions.append("job_title = %s")
            params.append(kwargs['job_title'])

        if 'manager' in kwargs:
            if kwargs['manager'] is None:
                conditions.append("manager IS NULL")
            else:
                conditions.append("manager = %s")
                params.append(kwargs['manager'])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT employee_id, name, email, phone, address, date_of_birth, ssn,
                   department, job_title, hire_date, manager, salary,
                   bank_account_number, routing_number, medical_condition
            FROM staff_pii
            WHERE {where_clause}
            ORDER BY employee_id
        """

        self.cursor.execute(query, params)
        return [self._row_to_staff(row) for row in self.cursor.fetchall()]

    def get_by_department(self, department: str) -> List[StaffPII]:
        """
        Get all employees in a specific department.

        This is a convenience method that wraps filter(department=...).

        Args:
            department: Department name to filter by

        Returns:
            List of StaffPII instances in the specified department

        Example:
            # Get all Engineering employees
            engineers = staff_repo.get_by_department("Engineering")
        """
        return self.filter(department=department)

    def search_by_email(self, email: str) -> Optional[StaffPII]:
        """
        Search for a staff record by email address.

        Args:
            email: Email address to search for

        Returns:
            StaffPII instance if found, None otherwise
        """
        query = """
            SELECT employee_id, name, email, phone, address, date_of_birth, ssn,
                   department, job_title, hire_date, manager, salary,
                   bank_account_number, routing_number, medical_condition
            FROM staff_pii
            WHERE email = %s
        """
        self.cursor.execute(query, (email,))
        row = self.cursor.fetchone()
        return self._row_to_staff(row) if row else None

    def search_by_ssn(self, ssn: str) -> Optional[StaffPII]:
        """
        Search for a staff record by Social Security Number.

        Args:
            ssn: SSN to search for (format: XXX-XX-XXXX)

        Returns:
            StaffPII instance if found, None otherwise

        Warning:
            Critical PII field - use with appropriate access controls
        """
        query = """
            SELECT employee_id, name, email, phone, address, date_of_birth, ssn,
                   department, job_title, hire_date, manager, salary,
                   bank_account_number, routing_number, medical_condition
            FROM staff_pii
            WHERE ssn = %s
        """
        self.cursor.execute(query, (ssn,))
        row = self.cursor.fetchone()
        return self._row_to_staff(row) if row else None

    def get_direct_reports(self, manager_id: str) -> List[StaffPII]:
        """
        Get all employees who directly report to a specified manager.

        Args:
            manager_id: Employee ID of the manager

        Returns:
            List of StaffPII instances for direct reports (empty if none)

        Example:
            # Get all employees reporting to manager EMP001
            reports = staff_repo.get_direct_reports('EMP001')
        """
        query = """
            SELECT employee_id, name, email, phone, address, date_of_birth, ssn,
                   department, job_title, hire_date, manager, salary,
                   bank_account_number, routing_number, medical_condition
            FROM staff_pii
            WHERE manager = %s
            ORDER BY name
        """
        self.cursor.execute(query, (manager_id,))
        return [self._row_to_staff(row) for row in self.cursor.fetchall()]

    def get_managers(self) -> List[StaffPII]:
        """
        Get all managers in the organization.

        A manager is defined as:
        - An employee with no manager (top-level executives), OR
        - An employee who has at least one direct report

        Returns:
            List of StaffPII instances for all managers
        """
        query = """
            SELECT DISTINCT s.employee_id, s.name, s.email, s.phone, s.address,
                   s.date_of_birth, s.ssn, s.department, s.job_title, s.hire_date,
                   s.manager, s.salary, s.bank_account_number, s.routing_number,
                   s.medical_condition
            FROM staff_pii s
            WHERE s.manager IS NULL
               OR s.employee_id IN (
                   SELECT DISTINCT manager
                   FROM staff_pii
                   WHERE manager IS NOT NULL
               )
            ORDER BY s.name
        """
        self.cursor.execute(query)
        return [self._row_to_staff(row) for row in self.cursor.fetchall()]


class ClientRepository:
    """
    Repository for managing ClientPII records in the client_pii table.

    Provides CRUD operations and search functionality for customer data.
    """

    def __init__(self, cursor):
        """
        Initialize repository with database cursor.

        Args:
            cursor: psycopg2 cursor for executing database operations
        """
        self.cursor = cursor

    def _row_to_client(self, row: tuple) -> ClientPII:
        """
        Convert database row tuple to ClientPII dataclass instance.

        Args:
            row: Database row tuple in column order matching client_pii table schema

        Returns:
            ClientPII instance with data from the row

        Note:
            Date field (date_of_birth) is converted from date object to ISO format
            string to match dataclass expectations.
        """
        return ClientPII(
            record_id=row[0],
            name=row[1],
            email=row[2],
            phone=row[3],
            address=row[4],
            date_of_birth=row[5].isoformat() if isinstance(row[5], date) else row[5],
            salary=row[6],
            medical_condition=row[7],
            ssn=row[8],
            credit_card=row[9]
        )

    def create(self, client: ClientPII) -> str:
        """
        Insert a new client record into the database.

        Args:
            client: ClientPII instance to insert

        Returns:
            The record_id of the inserted record

        Raises:
            psycopg2.IntegrityError: If record_id already exists or constraint violated
        """
        query = """
            INSERT INTO client_pii (
                record_id, name, email, phone, address, date_of_birth,
                salary, medical_condition, ssn, credit_card
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        self.cursor.execute(query, (
            client.record_id,
            client.name,
            client.email,
            client.phone,
            client.address,
            client.date_of_birth,
            client.salary,
            client.medical_condition,
            client.ssn,
            client.credit_card
        ))
        return client.record_id

    def get_by_id(self, record_id: str) -> Optional[ClientPII]:
        """
        Fetch a client record by record ID.

        Args:
            record_id: The record ID to search for

        Returns:
            ClientPII instance if found, None otherwise
        """
        query = """
            SELECT record_id, name, email, phone, address, date_of_birth,
                   salary, medical_condition, ssn, credit_card
            FROM client_pii
            WHERE record_id = %s
        """
        self.cursor.execute(query, (record_id,))
        row = self.cursor.fetchone()
        return self._row_to_client(row) if row else None

    def update(self, client: ClientPII) -> bool:
        """
        Update an existing client record.

        Args:
            client: ClientPII instance with updated data (record_id must exist)

        Returns:
            True if record was updated, False if record_id not found
        """
        query = """
            UPDATE client_pii
            SET name = %s, email = %s, phone = %s, address = %s,
                date_of_birth = %s, salary = %s, medical_condition = %s,
                ssn = %s, credit_card = %s
            WHERE record_id = %s
        """
        self.cursor.execute(query, (
            client.name,
            client.email,
            client.phone,
            client.address,
            client.date_of_birth,
            client.salary,
            client.medical_condition,
            client.ssn,
            client.credit_card,
            client.record_id
        ))
        return self.cursor.rowcount > 0

    def delete(self, record_id: str) -> bool:
        """
        Delete a client record by record ID.

        Args:
            record_id: The record ID to delete

        Returns:
            True if record was deleted, False if record_id not found
        """
        query = "DELETE FROM client_pii WHERE record_id = %s"
        self.cursor.execute(query, (record_id,))
        return self.cursor.rowcount > 0

    def list_all(self, limit: int = 100) -> List[ClientPII]:
        """
        Retrieve all client records with optional limit.

        Args:
            limit: Maximum number of records to return (default: 100)

        Returns:
            List of ClientPII instances
        """
        query = """
            SELECT record_id, name, email, phone, address, date_of_birth,
                   salary, medical_condition, ssn, credit_card
            FROM client_pii
            ORDER BY record_id
            LIMIT %s
        """
        self.cursor.execute(query, (limit,))
        return [self._row_to_client(row) for row in self.cursor.fetchall()]

    def get_all(self, limit: Optional[int] = None) -> List[ClientPII]:
        """
        Retrieve all client records with optional limit.

        Args:
            limit: Maximum number of records to return (default: None, returns all)

        Returns:
            List of ClientPII instances
        """
        if limit is None:
            query = """
                SELECT record_id, name, email, phone, address, date_of_birth,
                       salary, medical_condition, ssn, credit_card
                FROM client_pii
                ORDER BY record_id
            """
            self.cursor.execute(query)
        else:
            query = """
                SELECT record_id, name, email, phone, address, date_of_birth,
                       salary, medical_condition, ssn, credit_card
                FROM client_pii
                ORDER BY record_id
                LIMIT %s
            """
            self.cursor.execute(query, (limit,))
        return [self._row_to_client(row) for row in self.cursor.fetchall()]

    def filter(self, **kwargs) -> List[ClientPII]:
        """
        Filter client records by specified field criteria.

        Supported filters:
            - salary_min: Salary >= specified value
            - salary_max: Salary <= specified value
            - medical_condition: Exact match on medical condition

        Args:
            **kwargs: Field filters (e.g., salary_min=50000, medical_condition='Diabetes')

        Returns:
            List of ClientPII instances matching all specified criteria

        Examples:
            # Income range
            client_repo.filter(salary_min=50000, salary_max=100000)

            # Specific medical condition
            client_repo.filter(medical_condition='Diabetes')

            # Combined filters
            client_repo.filter(medical_condition='Diabetes', salary_min=60000)
        """
        conditions = []
        params = []

        if 'salary_min' in kwargs:
            conditions.append("salary >= %s")
            params.append(kwargs['salary_min'])

        if 'salary_max' in kwargs:
            conditions.append("salary <= %s")
            params.append(kwargs['salary_max'])

        if 'medical_condition' in kwargs:
            conditions.append("medical_condition = %s")
            params.append(kwargs['medical_condition'])

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT record_id, name, email, phone, address, date_of_birth,
                   salary, medical_condition, ssn, credit_card
            FROM client_pii
            WHERE {where_clause}
            ORDER BY record_id
        """

        self.cursor.execute(query, params)
        return [self._row_to_client(row) for row in self.cursor.fetchall()]

    def search_by_email(self, email: str) -> Optional[ClientPII]:
        """
        Search for a client record by email address.

        Args:
            email: Email address to search for

        Returns:
            ClientPII instance if found, None otherwise
        """
        query = """
            SELECT record_id, name, email, phone, address, date_of_birth,
                   salary, medical_condition, ssn, credit_card
            FROM client_pii
            WHERE email = %s
        """
        self.cursor.execute(query, (email,))
        row = self.cursor.fetchone()
        return self._row_to_client(row) if row else None

    def search_by_ssn(self, ssn: str) -> Optional[ClientPII]:
        """
        Search for a client record by Social Security Number.

        Args:
            ssn: SSN to search for (format: XXX-XX-XXXX)

        Returns:
            ClientPII instance if found, None otherwise

        Warning:
            Critical PII field - use with appropriate access controls
        """
        query = """
            SELECT record_id, name, email, phone, address, date_of_birth,
                   salary, medical_condition, ssn, credit_card
            FROM client_pii
            WHERE ssn = %s
        """
        self.cursor.execute(query, (ssn,))
        row = self.cursor.fetchone()
        return self._row_to_client(row) if row else None
