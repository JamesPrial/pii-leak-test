#!/usr/bin/env python3
"""
PostgreSQL Data Loader for PII Testing Database

This script loads synthetic staff and client PII records from JSON files into a PostgreSQL database.
It uses a truncate-and-reload strategy with proper foreign key constraint handling.

Usage:
    python3 load_data.py [options]
    ./load_data.py [options]

Options:
    --staff-file PATH      Path to staff records JSON file (default: outputs/test_staff_records.json)
    --client-file PATH     Path to client records JSON file (default: outputs/client_records.json)
    --skip-staff          Skip loading staff records
    --skip-client         Skip loading client records
    --verbose             Enable verbose logging
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Any, Optional

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection, cursor as pg_cursor
from dotenv import load_dotenv


# Configure logging
logger = logging.getLogger(__name__)


def load_json_file(filepath: str) -> List[Dict[str, Any]]:
    """
    Load JSON data from a file.

    Args:
        filepath: Path to the JSON file

    Returns:
        List of records as dictionaries

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    logger.info(f"Loading JSON file: {filepath}")

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} records from {filepath}")
    return data


def get_db_connection() -> connection:
    """
    Establish a connection to the PostgreSQL database using environment variables.

    Environment Variables:
        POSTGRES_USER: Database user (default: postgres)
        POSTGRES_PASSWORD: Database password (required)
        POSTGRES_DB: Database name (default: pii_test_db)
        POSTGRES_HOST: Database host (default: localhost)
        POSTGRES_PORT: Database port (default: 5432)

    Returns:
        psycopg2 connection object

    Raises:
        psycopg2.Error: If connection fails
    """
    # Get connection parameters from environment
    db_user = os.getenv('POSTGRES_USER', 'postgres')
    db_password = os.getenv('POSTGRES_PASSWORD')
    db_name = os.getenv('POSTGRES_DB', 'pii_test_db')
    db_host = os.getenv('POSTGRES_HOST', 'localhost')
    db_port = os.getenv('POSTGRES_PORT', '5432')

    if not db_password:
        raise ValueError("POSTGRES_PASSWORD environment variable is required")

    logger.info(f"Connecting to PostgreSQL database: {db_name} at {db_host}:{db_port}")

    conn = psycopg2.connect(
        user=db_user,
        password=db_password,
        database=db_name,
        host=db_host,
        port=db_port
    )

    logger.info("Successfully connected to database")
    return conn


def truncate_tables(cursor: pg_cursor) -> None:
    """
    Truncate both staff_pii and client_pii tables with CASCADE.

    This removes all data from both tables and resets sequences.
    The CASCADE option ensures dependent rows are also removed.

    Args:
        cursor: Database cursor
    """
    logger.info("Truncating tables...")

    # Truncate both tables with CASCADE to handle dependencies
    cursor.execute("TRUNCATE TABLE staff_pii, client_pii CASCADE;")

    logger.info("Tables truncated successfully")


def load_staff_records(cursor: pg_cursor, records: List[Dict[str, Any]]) -> int:
    """
    Load staff PII records into the database using a two-phase approach.

    Phase 1: Insert all records with manager=NULL
    Phase 2: Update manager references

    This approach avoids foreign key violations when managers reference other staff members.

    Args:
        cursor: Database cursor
        records: List of staff record dictionaries

    Returns:
        Number of records loaded
    """
    logger.info(f"Loading {len(records)} staff records...")

    # Phase 1: Insert all records with manager=NULL
    insert_query = """
        INSERT INTO staff_pii (
            employee_id, first_name, last_name, date_of_birth, ssn,
            email, phone, address, department, job_title,
            hire_date, salary, medical_condition, manager
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, NULL
        )
    """

    for record in records:
        cursor.execute(insert_query, (
            record['employee_id'],
            record['first_name'],
            record['last_name'],
            record['date_of_birth'],
            record['ssn'],
            record['email'],
            record['phone'],
            record['address'],
            record['department'],
            record['job_title'],
            record['hire_date'],
            record['salary'],
            record.get('medical_condition', 'None')
        ))

    logger.info(f"Phase 1 complete: Inserted {len(records)} staff records")

    # Phase 2: Update manager references
    update_query = """
        UPDATE staff_pii
        SET manager = %s
        WHERE employee_id = %s
    """

    manager_updates = 0
    for record in records:
        if record.get('manager'):
            cursor.execute(update_query, (
                record['manager'],
                record['employee_id']
            ))
            manager_updates += 1

    logger.info(f"Phase 2 complete: Updated {manager_updates} manager references")
    logger.info(f"Successfully loaded {len(records)} staff records")

    return len(records)


def load_client_records(cursor: pg_cursor, records: List[Dict[str, Any]]) -> int:
    """
    Load client PII records into the database.

    Args:
        cursor: Database cursor
        records: List of client record dictionaries

    Returns:
        Number of records loaded
    """
    logger.info(f"Loading {len(records)} client records...")

    insert_query = """
        INSERT INTO client_pii (
            first_name, last_name, date_of_birth, ssn, email,
            phone, address, credit_card, bank_account, medical_condition
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
    """

    for record in records:
        cursor.execute(insert_query, (
            record['first_name'],
            record['last_name'],
            record['date_of_birth'],
            record['ssn'],
            record['email'],
            record['phone'],
            record['address'],
            record['credit_card'],
            record['bank_account'],
            record.get('medical_condition', 'None')
        ))

    logger.info(f"Successfully loaded {len(records)} client records")
    return len(records)


def main():
    """
    Main entry point for the data loader script.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Load PII test data into PostgreSQL database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--staff-file',
        default='outputs/test_staff_records.json',
        help='Path to staff records JSON file (default: outputs/test_staff_records.json)'
    )
    parser.add_argument(
        '--client-file',
        default='outputs/client_records.json',
        help='Path to client records JSON file (default: outputs/client_records.json)'
    )
    parser.add_argument(
        '--skip-staff',
        action='store_true',
        help='Skip loading staff records'
    )
    parser.add_argument(
        '--skip-client',
        action='store_true',
        help='Skip loading client records'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load environment variables from .env file
    load_dotenv()

    # Check if at least one data source is specified
    if args.skip_staff and args.skip_client:
        logger.error("Both --skip-staff and --skip-client specified. Nothing to load.")
        sys.exit(1)

    conn: Optional[connection] = None
    staff_count = 0
    client_count = 0

    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Start transaction with deferred constraints
        cursor.execute("SET CONSTRAINTS ALL DEFERRED;")
        logger.info("Set constraints to deferred mode")

        # Truncate tables
        truncate_tables(cursor)

        # Load staff records
        if not args.skip_staff:
            try:
                staff_records = load_json_file(args.staff_file)
                staff_count = load_staff_records(cursor, staff_records)
            except FileNotFoundError as e:
                logger.error(f"Staff file error: {e}")
                raise
            except Exception as e:
                logger.error(f"Error loading staff records: {e}")
                raise
        else:
            logger.info("Skipping staff records (--skip-staff)")

        # Load client records
        if not args.skip_client:
            try:
                client_records = load_json_file(args.client_file)
                client_count = load_client_records(cursor, client_records)
            except FileNotFoundError as e:
                logger.error(f"Client file error: {e}")
                raise
            except Exception as e:
                logger.error(f"Error loading client records: {e}")
                raise
        else:
            logger.info("Skipping client records (--skip-client)")

        # Commit transaction (re-enables constraints)
        conn.commit()
        logger.info("Transaction committed successfully")

        # Print summary
        logger.info("=" * 60)
        logger.info("DATA LOAD SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Staff records loaded:  {staff_count:>6}")
        logger.info(f"Client records loaded: {client_count:>6}")
        logger.info(f"Total records loaded:  {staff_count + client_count:>6}")
        logger.info("=" * 60)

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
            logger.info("Transaction rolled back")
        sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        if conn:
            conn.rollback()
            logger.info("Transaction rolled back")
        sys.exit(1)

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        if conn:
            conn.rollback()
            logger.info("Transaction rolled back")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if conn:
            conn.rollback()
            logger.info("Transaction rolled back")
        sys.exit(1)

    finally:
        # Close database connection
        if conn:
            conn.close()
            logger.info("Database connection closed")


if __name__ == '__main__':
    main()
