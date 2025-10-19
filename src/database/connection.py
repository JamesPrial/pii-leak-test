#!/usr/bin/env python3
"""
Database Connection Manager for PII Testing PostgreSQL Database

This module provides a context manager for safely handling PostgreSQL database connections
with automatic transaction management, connection cleanup, and comprehensive error handling.

Usage:
    Basic usage with automatic commit/rollback:
        ```python
        from connection import DatabaseConnection

        with DatabaseConnection() as db_conn:
            cursor = db_conn.cursor
            cursor.execute("SELECT * FROM staff_pii LIMIT 5")
            results = cursor.fetchall()
            for row in results:
                print(row)
        # Connection automatically commits on success, rolls back on exception
        ```

    Multiple operations in a single transaction:
        ```python
        with DatabaseConnection() as db_conn:
            cursor = db_conn.cursor

            # All operations are part of the same transaction
            cursor.execute("INSERT INTO staff_pii (...) VALUES (...)")
            cursor.execute("UPDATE staff_pii SET ... WHERE ...")
            cursor.execute("DELETE FROM client_pii WHERE ...")
        # All changes committed together, or all rolled back if any operation fails
        ```

    Accessing the connection object directly:
        ```python
        with DatabaseConnection() as db_conn:
            conn = db_conn.connection
            cursor = db_conn.cursor

            # Direct connection access for advanced operations
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)
            cursor.execute("SELECT * FROM staff_pii")
        ```

Environment Variables:
    POSTGRES_USER: Database user (default: postgres)
    POSTGRES_PASSWORD: Database password (required)
    POSTGRES_DB: Database name (default: pii_test_db)
    POSTGRES_HOST: Database host (default: localhost)
    POSTGRES_PORT: Database port (default: 5432)

Example .env file:
    POSTGRES_USER=pii_admin
    POSTGRES_PASSWORD=secure_password_here
    POSTGRES_DB=pii_test_data
    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
"""

import os
from pathlib import Path
from typing import Optional

import psycopg2
from psycopg2.extensions import connection as pg_connection, cursor as pg_cursor
from dotenv import load_dotenv


class DatabaseConnection:
    """
    Context manager for PostgreSQL database connections with automatic transaction management.

    This class provides a safe and convenient way to handle database connections with:
    - Automatic connection establishment from environment variables
    - Transaction safety: auto-commit on success, auto-rollback on exception
    - Guaranteed connection cleanup in all cases
    - Access to both connection and cursor objects

    Attributes:
        connection (psycopg2.extensions.connection): The PostgreSQL connection object
        cursor (psycopg2.extensions.cursor): The database cursor for executing queries

    Raises:
        ValueError: If required environment variables are missing
        psycopg2.Error: If database connection or operations fail

    Example:
        ```python
        # Load environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv()

        # Use the connection manager
        with DatabaseConnection() as db_conn:
            cursor = db_conn.cursor
            cursor.execute("SELECT COUNT(*) FROM staff_pii")
            count = cursor.fetchone()[0]
            print(f"Total staff records: {count}")
        ```
    """

    def __init__(self):
        """
        Initialize the DatabaseConnection manager.

        Note: The actual database connection is not established until __enter__ is called
        (i.e., when entering the context manager with the 'with' statement).
        """
        self.connection: Optional[pg_connection] = None
        self.cursor: Optional[pg_cursor] = None

    def __enter__(self) -> 'DatabaseConnection':
        """
        Enter the context manager and establish database connection.

        This method:
        1. Loads environment variables for database configuration
        2. Validates required environment variables
        3. Establishes a connection to the PostgreSQL database
        4. Creates a cursor for executing queries

        Returns:
            DatabaseConnection: The initialized connection manager with active connection

        Raises:
            ValueError: If POSTGRES_PASSWORD environment variable is not set
            psycopg2.Error: If connection to the database fails
        """
        # Load environment variables from .env file if present
        # Use module directory to ensure .env is found regardless of working directory
        env_path = Path(__file__).parent / '.env'
        load_dotenv(env_path)

        # Get connection parameters from environment variables
        db_user = os.getenv('POSTGRES_USER', 'postgres')
        db_password = os.getenv('POSTGRES_PASSWORD')
        db_name = os.getenv('POSTGRES_DB', 'pii_test_db')
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        db_port = os.getenv('POSTGRES_PORT', '5432')

        # Validate required environment variables
        if not db_password:
            raise ValueError(
                "POSTGRES_PASSWORD environment variable is required. "
                "Please set it in your .env file or environment."
            )

        try:
            # Establish database connection
            self.connection = psycopg2.connect(
                user=db_user,
                password=db_password,
                database=db_name,
                host=db_host,
                port=db_port
            )

            # Create a cursor for executing queries
            self.cursor = self.connection.cursor()

            return self

        except psycopg2.Error as e:
            # If connection fails, ensure we don't leave partial state
            if self.connection:
                self.connection.close()
            raise psycopg2.Error(
                f"Failed to connect to database {db_name} at {db_host}:{db_port} "
                f"as user {db_user}: {e}"
            ) from e

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit the context manager and handle transaction cleanup.

        This method ensures proper cleanup in all cases:
        - If no exception occurred: commits the transaction
        - If an exception occurred: rolls back the transaction
        - In all cases: closes the cursor and connection

        Args:
            exc_type: Exception type if an exception was raised, None otherwise
            exc_val: Exception value if an exception was raised, None otherwise
            exc_tb: Exception traceback if an exception was raised, None otherwise

        Returns:
            bool: Always returns False to propagate any exceptions that occurred

        Note:
            This method always returns False to ensure exceptions are propagated
            to the caller for proper error handling.
        """
        try:
            if exc_type is None:
                # No exception occurred - commit the transaction
                if self.connection:
                    self.connection.commit()
            else:
                # An exception occurred - rollback the transaction
                if self.connection:
                    self.connection.rollback()
        finally:
            # Always close cursor and connection, regardless of commit/rollback success
            if self.cursor:
                try:
                    self.cursor.close()
                except Exception:
                    # Ignore errors during cursor cleanup
                    pass

            if self.connection:
                try:
                    self.connection.close()
                except Exception:
                    # Ignore errors during connection cleanup
                    pass

        # Return False to propagate any exceptions
        return False


# Example usage and demonstration
if __name__ == '__main__':
    """
    Demonstration of DatabaseConnection usage.

    This example shows basic usage patterns including successful operations
    and error handling.
    """
    import sys

    print("DatabaseConnection Manager - Usage Examples")
    print("=" * 60)

    try:
        # Example 1: Simple query
        print("\n1. Simple SELECT query:")
        with DatabaseConnection() as db_conn:
            cursor = db_conn.cursor
            cursor.execute("SELECT COUNT(*) FROM staff_pii")
            count = cursor.fetchone()[0]
            print(f"   Total staff records: {count}")
        print("   Transaction committed successfully")

        # Example 2: Multiple operations
        print("\n2. Multiple operations in one transaction:")
        with DatabaseConnection() as db_conn:
            cursor = db_conn.cursor

            cursor.execute("SELECT COUNT(*) FROM staff_pii")
            staff_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM client_pii")
            client_count = cursor.fetchone()[0]

            print(f"   Staff records: {staff_count}")
            print(f"   Client records: {client_count}")
            print(f"   Total records: {staff_count + client_count}")
        print("   Transaction committed successfully")

        # Example 3: Error handling - automatic rollback
        print("\n3. Error handling (automatic rollback on exception):")
        try:
            with DatabaseConnection() as db_conn:
                cursor = db_conn.cursor
                cursor.execute("SELECT * FROM nonexistent_table")
        except psycopg2.Error as e:
            print(f"   Expected error occurred: {type(e).__name__}")
            print("   Transaction automatically rolled back")

        print("\n" + "=" * 60)
        print("All examples completed successfully")

    except ValueError as e:
        print(f"\nConfiguration error: {e}", file=sys.stderr)
        print("\nPlease ensure your .env file is configured correctly.", file=sys.stderr)
        sys.exit(1)

    except psycopg2.Error as e:
        print(f"\nDatabase error: {e}", file=sys.stderr)
        print("\nPlease ensure PostgreSQL is running and accessible.", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"\nUnexpected error: {e}", file=sys.stderr)
        sys.exit(1)
