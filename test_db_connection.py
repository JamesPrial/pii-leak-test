#!/usr/bin/env python3
"""
Simple script to test database connectivity from Python.
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_connection():
    """Test PostgreSQL connection using psycopg2."""
    try:
        # Get connection parameters from environment
        conn_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'user': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'database': os.getenv('POSTGRES_DB')
        }

        print(f"Connecting to PostgreSQL at {conn_params['host']}:{conn_params['port']}...")
        print(f"Database: {conn_params['database']}, User: {conn_params['user']}")

        # Establish connection
        conn = psycopg2.connect(**conn_params)
        print("✓ Connection established successfully!")

        # Create cursor and execute test query
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"✓ PostgreSQL version: {version}")

        # Test table access
        cur.execute("SELECT COUNT(*) FROM staff_pii;")
        staff_count = cur.fetchone()[0]
        print(f"✓ staff_pii table accessible (rows: {staff_count})")

        cur.execute("SELECT COUNT(*) FROM client_pii;")
        client_count = cur.fetchone()[0]
        print(f"✓ client_pii table accessible (rows: {client_count})")

        # Test insert and rollback
        cur.execute("""
            INSERT INTO staff_pii (
                employee_id, name, email, phone, address, date_of_birth, ssn,
                department, job_title, hire_date, salary, bank_account_number,
                routing_number
            ) VALUES (
                'TEST001', 'Test User', 'test@example.com', '555-0100',
                '123 Test St', '1990-01-01', '123-45-6789',
                'Engineering', 'Test Engineer', '2020-01-01', 100000,
                '123456789', '021000021'
            );
        """)
        print("✓ Test insert successful (will rollback)")

        # Rollback to keep database clean
        conn.rollback()
        print("✓ Rollback successful")

        # Clean up
        cur.close()
        conn.close()
        print("✓ Connection closed")

        print("\n" + "="*60)
        print("DATABASE CONNECTIVITY TEST: PASSED")
        print("="*60)
        return True

    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\n" + "="*60)
        print("DATABASE CONNECTIVITY TEST: FAILED")
        print("="*60)
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
