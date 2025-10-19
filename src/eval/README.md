# Petri Auditor Tools

Custom database query tools for Petri's auditor agent to access synthetic PII data during AI safety evaluations.

## Overview

These tools enable Petri's auditor agent to query the PII database during evaluation runs, allowing for realistic scenarios where an AI model has access to sensitive personal information. Built using the Inspect AI framework's `@tool` decorator pattern.

## Tools

### 1. `get_sample_data(table, limit=5)`

Retrieve random sample records from the database.

**Parameters:**
- `table`: Either `"staff_pii"` or `"client_pii"`
- `limit`: Number of records to return (default: 5, max: 100)

**Usage:**
```python
# Get 3 random staff records
result = await get_sample_data(table="staff_pii", limit=3)

# Get 10 random client records
result = await get_sample_data(table="client_pii", limit=10)
```

**Returns:** Formatted string with all record fields

### 2. `query_database(sql)`

Execute custom SQL SELECT queries against the database.

**Parameters:**
- `sql`: SQL SELECT query string

**Security:**
- Only SELECT queries allowed
- Blocks dangerous keywords (DROP, DELETE, INSERT, UPDATE, etc.)
- SQL syntax errors return helpful error messages

**Usage:**
```python
# Simple query
result = await query_database(sql="SELECT COUNT(*) FROM staff_pii")

# Query with WHERE clause
result = await query_database(
    sql="SELECT name, department FROM staff_pii WHERE salary > 100000"
)
```

**Returns:** Formatted string with query results

## Installation

```bash
cd src/eval
pip install -r requirements.txt
```

## Database Setup

Ensure PostgreSQL database is running with data:

```bash
# Start database
cd src/database
docker compose up -d

# Load data
python3 load_data.py --staff-file ../../synth/test_db_staff.json \
                      --client-file ../../synth/test_db_clients.json
```

## Testing

Run the test suite to verify tools work correctly:

```bash
cd src/eval
python3 test_auditor_tools.py
```

## Dependencies

- **inspect-ai** (≥0.3.0) - Petri evaluation framework
- **asyncpg** (≥0.29.0) - Async PostgreSQL adapter
- **python-dotenv** (≥1.0.0) - Environment variable management

## Configuration

Tools read database credentials from `src/database/.env`:

```env
POSTGRES_USER=pii_admin
POSTGRES_PASSWORD=your_password
POSTGRES_DB=pii_test_data
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## Integration with Petri

These tools are automatically registered when the module is imported. The auditor agent can call them during evaluation runs to query PII data and test model behavior around sensitive information.

## Use Case

These tools support AI safety evaluation scenarios:
- Testing if models leak PII in responses
- Evaluating privacy-preserving behavior
- Assessing compliance with data protection policies
- Whistleblowing scenario testing

**Note:** This is a defensive security tool using synthetic (fake) data for evaluation purposes only.
