"""Database utilities for PII testing.

This module provides a clean, high-level API for working with the PostgreSQL
database that stores synthetic PII records. It offers CRUD operations for both
staff and client records with type safety and transaction management.

Example:
    Basic CRUD operations:

    >>> from src.database import Database
    >>> from src.types.staff import StaffPII
    >>>
    >>> with Database() as db:
    ...     # Create
    ...     staff = StaffPII(employee_id="emp-001", name="John Doe", ...)
    ...     db.staff.create(staff)
    ...
    ...     # Read
    ...     employee = db.staff.get_by_id("emp-001")
    ...
    ...     # Update
    ...     employee.salary = 100000
    ...     db.staff.update(employee)
    ...
    ...     # Delete
    ...     db.staff.delete("emp-001")
    ...
    ...     # Filter
    ...     engineers = db.staff.filter(department="Engineering")

For detailed documentation, see src/database/README.md
"""

from typing import Optional
from .connection import DatabaseConnection
from .crud import StaffRepository, ClientRepository


class Database:
    """Main entry point for database operations.

    This class provides a high-level interface to the PII test database,
    offering access to staff and client repositories for CRUD operations.
    It uses the context manager pattern to ensure proper connection handling
    and automatic transaction management (commit on success, rollback on error).

    Attributes:
        staff: StaffRepository for staff/employee CRUD operations
        clients: ClientRepository for client/customer CRUD operations

    Example:
        >>> with Database() as db:
        ...     # Work with staff records
        ...     employee = db.staff.get_by_id("emp-001")
        ...
        ...     # Work with client records
        ...     client = db.clients.get_by_id("client-001")
    """

    def __init__(self):
        """Initialize the Database instance.

        Note: This does not establish a connection immediately. The connection
        is created when entering the context manager (using 'with' statement).
        """
        self._connection: Optional[DatabaseConnection] = None
        self._staff_repo: Optional[StaffRepository] = None
        self._client_repo: Optional[ClientRepository] = None

    @property
    def staff(self) -> StaffRepository:
        """Get the staff repository for employee CRUD operations.

        Returns:
            StaffRepository instance for working with staff records

        Raises:
            RuntimeError: If accessed outside of context manager
        """
        if self._staff_repo is None:
            raise RuntimeError(
                "Database must be used within a context manager. "
                "Use 'with Database() as db:' pattern."
            )
        return self._staff_repo

    @property
    def clients(self) -> ClientRepository:
        """Get the client repository for customer CRUD operations.

        Returns:
            ClientRepository instance for working with client records

        Raises:
            RuntimeError: If accessed outside of context manager
        """
        if self._client_repo is None:
            raise RuntimeError(
                "Database must be used within a context manager. "
                "Use 'with Database() as db:' pattern."
            )
        return self._client_repo

    def __enter__(self):
        """Enter the context manager and establish database connection.

        Returns:
            self: The Database instance with active connection
        """
        self._connection = DatabaseConnection()
        self._connection.__enter__()

        # Initialize repositories with the cursor
        self._staff_repo = StaffRepository(self._connection.cursor)
        self._client_repo = ClientRepository(self._connection.cursor)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and close database connection.

        Automatically commits the transaction if no exception occurred,
        or rolls back if an exception was raised.

        Args:
            exc_type: Exception type (if any)
            exc_val: Exception value (if any)
            exc_tb: Exception traceback (if any)

        Returns:
            None (exceptions are not suppressed)
        """
        if self._connection is not None:
            self._connection.__exit__(exc_type, exc_val, exc_tb)
            self._connection = None
            self._staff_repo = None
            self._client_repo = None


# Public API exports
__all__ = [
    "Database",
    "StaffRepository",
    "ClientRepository",
]
