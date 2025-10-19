#!/usr/bin/env python3
"""
Test script for Petri auditor tools

Simple test to verify the database tools work correctly.
Run this after starting the PostgreSQL database with docker compose.

Usage:
    cd src/eval
    python3 test_auditor_tools.py
"""

import asyncio
from auditor_tools import get_sample_data, query_database


async def test_get_sample_data():
    """Test the get_sample_data tool."""
    print("=" * 60)
    print("Testing get_sample_data tool")
    print("=" * 60)

    # Get the tool's execute function
    sample_tool = get_sample_data()

    # Test 1: Get sample staff data
    print("\n1. Testing staff_pii sample (3 records):")
    try:
        result = await sample_tool(table="staff_pii", limit=3)
        print(result)
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 2: Get sample client data
    print("\n2. Testing client_pii sample (2 records):")
    try:
        result = await sample_tool(table="client_pii", limit=2)
        print(result)
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 3: Invalid limit
    print("\n3. Testing invalid limit (should fail):")
    try:
        result = await sample_tool(table="staff_pii", limit=0)
        print(result)
    except Exception as e:
        print(f"Expected error: {e}")


async def test_query_database():
    """Test the query_database tool."""
    print("\n" + "=" * 60)
    print("Testing query_database tool")
    print("=" * 60)

    # Get the tool's execute function
    query_tool = query_database()

    # Test 1: Simple SELECT query
    print("\n1. Testing simple SELECT (count staff):")
    try:
        result = await query_tool(sql="SELECT COUNT(*) as total_staff FROM staff_pii")
        print(result)
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 2: Query with WHERE clause
    print("\n2. Testing SELECT with WHERE clause:")
    try:
        result = await query_tool(
            sql="SELECT name, department, job_title FROM staff_pii LIMIT 3"
        )
        print(result)
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 3: Invalid query (should fail - not a SELECT)
    print("\n3. Testing forbidden query type (should fail):")
    try:
        result = await query_tool(sql="DELETE FROM staff_pii")
        print(result)
    except Exception as e:
        print(f"Expected error: {e}")

    # Test 4: Query with syntax error
    print("\n4. Testing SQL syntax error (should fail):")
    try:
        result = await query_tool(sql="SELECT * FROM nonexistent_table")
        print(result)
    except Exception as e:
        print(f"Expected error: {e}")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PETRI AUDITOR TOOLS TEST SUITE")
    print("=" * 60)
    print("\nMake sure PostgreSQL database is running:")
    print("  cd ../database && docker compose up -d\n")

    await test_get_sample_data()
    await test_query_database()

    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
