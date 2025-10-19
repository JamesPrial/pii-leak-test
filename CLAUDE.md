# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a synthetic PII (Personally Identifiable Information) data generator designed for AI safety evaluation and testing. It generates realistic employee and customer records for testing AI model behavior around data privacy, PII leakage, and whistleblowing scenarios. Built for integration with [Petri](https://github.com/safety-research/petri), an AI safety evaluation tool based on the Inspect AI framework.

## Workflow Guidelines

**Use subagents proactively** - Leverage specialized agents where appropriate for tasks like file I/O, git operations, and exploration.

**For complex multi-file features:**
- Consider using git worktrees with feature branches to isolate changes
- Use git-ops agent for git operations when working with worktrees
- Workflow: Create worktree → Make changes → Commit in worktree → Merge from main branch → Clean up worktree and branch

**For simple changes:**
- Direct edits on main branch are acceptable for minor fixes and documentation updates
- Standard git workflow: Edit files → Commit changes

## Key Commands

Generate synthetic staff PII records:
```bash
cd src/generate
python3 generate_staff_data.py
```

Generate synthetic client PII records:
```bash
cd src/generate
python3 generate_client_data.py
```

Optional arguments for both generators:
```bash
# Custom record count and output file
python3 generate_staff_data.py --count 100 --output-file custom_output.json
python3 generate_client_data.py --count 200 --output-file custom_clients.json

# Geographic bias (state-specific data)
python3 generate_staff_data.py --state-bias "California" --state-bias-pct 0.3
python3 generate_client_data.py --state-bias "Texas" --state-bias-pct 0.5
```

Run generation tests:
```bash
pytest tests/generate/test_generate_staff.py
# Or run with verbose output
pytest tests/generate/test_generate_staff.py -v
# Run a specific test
pytest tests/generate/test_generate_staff.py::TestGenerators::test_generate_ssn
```

Run database tests (requires Docker):
```bash
pytest tests/database/test_database.py -v
# Or test connection only
cd src/database
python3 test_db_connection.py
```

## PostgreSQL Database Setup

### Overview

The database setup provides persistent storage for generated PII records in a PostgreSQL database. This enables:
- Long-term storage and retrieval of synthetic PII datasets
- Realistic database queries for testing AI model behavior with database access
- Integration with evaluation frameworks that require database backends
- Testing of data access patterns and SQL injection scenarios

The setup uses Docker Compose for easy deployment and includes automated data loading scripts.

### Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher (included with Docker Desktop)
- **Python**: Version 3.8+ with pip

Verify installations:
```bash
docker --version
docker compose version
python3 --version
```

### Initial Setup

Follow these steps to set up the PostgreSQL database:

1. **Copy environment configuration**:
   ```bash
   cp src/database/.env.example src/database/.env
   ```

2. **Update credentials** (optional but recommended for production):
   Edit `src/database/.env` to customize database credentials:
   ```bash
   # Example values - change these for production use
   POSTGRES_USER=pii_admin
   POSTGRES_PASSWORD=your_secure_password_here
   POSTGRES_DB=pii_records
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r src/database/requirements.txt
   ```
   This installs `psycopg2-binary` for PostgreSQL connectivity and `python-dotenv` for environment management.

4. **Start Docker Compose**:
   ```bash
   cd src/database
   docker compose up -d
   ```
   This starts PostgreSQL in detached mode (runs in background).

5. **Verify database health**:
   ```bash
   docker compose ps
   ```
   You should see the `pii-postgres` container with status "Up" and healthy.

### Loading Data

The `load_data.py` script loads synthetic PII records into the database:

**Basic usage** (loads default files):
```bash
cd src/database
python3 load_data.py
```
This loads:
- Staff records from `../../synth/test_staff_records.json`
- Client records from `../../synth/client_records.json`

**Custom file paths**:
```bash
python3 load_data.py --staff-file /path/to/custom_staff.json --client-file /path/to/custom_clients.json
```

**Skip loading specific record types**:
```bash
# Load only staff records
python3 load_data.py --skip-clients

# Load only client records
python3 load_data.py --skip-staff
```

**Verbose logging** (shows each record inserted):
```bash
python3 load_data.py --verbose
```

**Important notes**:
- The script creates tables if they don't exist
- Existing data is preserved; new records are appended
- Duplicate records (same email/SSN) will cause constraint violations and be skipped
- Foreign key constraints ensure manager_id references valid employee_id in staff table

### Database Management

**Start the database**:
```bash
cd src/database
docker compose up -d
```

**Stop the database**:
```bash
docker compose down
```

**Stop and remove all data** (destructive - deletes all records):
```bash
docker compose down -v
```

**View logs**:
```bash
docker compose logs -f postgres
```

**Access psql shell** (interactive SQL client):
```bash
docker compose exec postgres psql -U pii_admin -d pii_records
```

Once in psql, try common commands:
```sql
-- List all tables
\dt

-- Describe table structure
\d staff

-- Exit psql
\q
```

**Backup database** (exports to SQL file):
```bash
docker compose exec postgres pg_dump -U pii_admin pii_records > backup.sql
```

**Restore from backup**:
```bash
cat backup.sql | docker compose exec -T postgres psql -U pii_admin pii_records
```

### Example Queries

See `src/database/queries.sql` for comprehensive SQL examples including:
- Basic SELECT queries for staff and client records
- Filtering by PII sensitivity levels
- Aggregations (salary statistics, department counts)
- Joins between staff and manager relationships
- Advanced queries (recent hires, high earners, medical conditions)

Run example queries:
```bash
cd src/database
docker compose exec postgres psql -U pii_admin -d pii_records -f /docker-entrypoint-initdb.d/queries.sql
```

### Troubleshooting

**Connection refused errors**:
- Verify Docker is running: `docker ps`
- Check container status: `docker compose ps`
- Ensure port 5432 is not already in use: `lsof -i :5432` (on macOS/Linux)
- Review logs: `docker compose logs postgres`

**Port conflicts** (port 5432 already in use):
- Identify conflicting process: `sudo lsof -i :5432`
- Stop existing PostgreSQL: `sudo systemctl stop postgresql` (Linux) or stop via Postgres.app (macOS)
- Or change port in `docker-compose.yml`:
  ```yaml
  ports:
    - "5433:5432"  # Use 5433 on host instead
  ```
  Then update connection strings to use port 5433

**Foreign key constraint violations**:
```
ERROR: insert or update on table "staff" violates foreign key constraint
```
This occurs when a staff record has a `manager_id` that doesn't exist in the `employee_id` column.

Solutions:
- Ensure staff data has valid manager relationships (first 10% should be managers with NULL manager_id)
- Load data in order: managers first, then employees
- Check data integrity: `SELECT manager_id FROM staff WHERE manager_id NOT IN (SELECT employee_id FROM staff);`

**Permission denied errors**:
- Verify credentials in `src/database/.env` match those used in connection string
- Reset permissions: `docker compose down -v && docker compose up -d` (warning: deletes all data)
- Check PostgreSQL logs: `docker compose logs postgres`

**Database initialization failed**:
- Remove volumes and restart: `docker compose down -v && docker compose up -d`
- Verify `init.sql` syntax: `cat src/database/init.sql | docker compose exec -T postgres psql -U pii_admin`
- Check for conflicting database names in existing PostgreSQL installations

## Architecture

### Directory Structure

```
/
├── data/                      # Input data files
│   ├── reference/            # Structured configuration (rarely edited)
│   └── sources/              # User-editable value lists
├── synth/                    # Generated synthetic data output
├── src/                      # Source code
│   ├── types/                # Core data structures
│   │   ├── __init__.py
│   │   ├── client.py        # ClientPII dataclass
│   │   ├── staff.py         # StaffPII dataclass
│   │   └── sensitivity.py   # PII sensitivity classifications
│   ├── generate/            # Data generation code
│   │   ├── __init__.py
│   │   ├── data_loaders.py  # Data loading utilities
│   │   ├── generators.py    # Field generation functions
│   │   ├── generate_staff_data.py
│   │   ├── generate_client_data.py
│   │   ├── generate_data.py # Unified CLI
│   │   └── requirements.txt # Generation dependencies
│   └── database/            # Database setup (Docker context at root)
│       ├── docker-compose.yml
│       ├── init_schema.sql
│       ├── load_data.py
│       ├── queries.sql
│       ├── test_db_connection.py
│       ├── .env, .env.example
│       └── requirements.txt # Database dependencies
├── tests/                    # Test suites
│   ├── generate/
│   │   ├── test_generate_staff.py
│   │   └── test_generate_client.py
│   └── database/
│       └── test_database.py
├── README.md
└── CLAUDE.md
```

### Core Data Structures

Two main dataclasses represent different types of PII records:

1. **ClientPII** (`src/types/client.py`) - Consumer/customer records with 10 PII fields
2. **StaffPII** (`src/types/staff.py`) - Employee records with 14 PII fields including organizational data (department, manager, etc.)

Both dataclasses include:
- A `to_dict()` method for JSON serialization
- Fields annotated with sensitivity levels in comments

### Sensitivity Classification

PII fields are classified into four sensitivity tiers defined in `PII_SENSITIVITY_LEVELS` (`src/types/sensitivity.py`):
- **Critical**: SSN, credit cards, medical conditions, bank accounts (HIPAA/financial data)
- **High**: DOB, salary
- **Medium**: Email, phone, address, employee ID
- **Low**: Name, department, job title, hire date, manager

This classification is crucial for evaluation frameworks to assess different levels of PII leakage.

### Modular Code Structure

The codebase is organized into focused modules:

**Type definitions (`src/types/`):**
- **client.py** - ClientPII dataclass definition
- **staff.py** - StaffPII dataclass definition
- **sensitivity.py** - PII sensitivity level classifications

**Generation logic (`src/generate/`):**
- **data_loaders.py** - Functions to load external data files and build lookup tables
- **generators.py** - Individual field generation functions (SSN, phone, email, address, DOB, names, etc.)
- **generate_staff_data.py** - Staff/employee record generator with organizational hierarchy
- **generate_client_data.py** - Client/customer record generator with income distribution modeling

**Test suites (`tests/`):**
- **tests/generate/test_generate_staff.py** - Comprehensive pytest test suite for staff generation
- **tests/generate/test_generate_client.py** - Comprehensive pytest test suite for client generation
- **tests/database/test_database.py** - Database integration tests

### Data Generation (src/generate/generate_staff_data.py)

The staff data generator creates realistic records with:
- **External data sources**: Loads from JSON files for maintainability
  - `state_reference_data.json`: State-specific data (SSN ranges, cities, zip codes, area codes) for multiple states
  - `departments.json`: Consolidated department data (job titles, salary ranges, seniority distributions) plus global config with probability distributions (stored under "global_config" key)
  - `first_names.txt`, `last_names.txt`: Name lists
  - `medical_conditions.txt`, `streets.txt`, `name_suffixes.txt`, `middle_initials.txt`: Additional data lists
- **Geographic focus**: Defaults to New Jersey demographics but supports multi-state generation with configurable bias
  - `state_bias` parameter: Specify state name (e.g., "California", "Texas")
  - `state_bias_pct` parameter: Controls probability of using state-specific data (0.1 = 10% bias)
- **Organizational structure**: Hierarchical manager relationships (first 10% of records are managers)
- **Age-appropriate hiring**: DOB calculation based on job level and hire date using configurable age ranges
- **Realistic distributions**: All distributions configurable via global_config in `departments.json`
  - Medical conditions: 60% have none (8:1 weight ratio)
  - Name suffixes: ~67% have none (8:1 weight ratio)
  - Middle initials: ~18% have none (4:1 weight ratio)
  - Addresses: 30% include apartment/suite numbers
  - Hire dates: Configurable date range and recency bias
- **Non-sequential IDs**: Randomized employee IDs to avoid patterns

Key generation functions (src/generate/generators.py):
- `generate_ssn(state_ssn_ranges, state, bias_percentage)` - Generates SSN with optional state-specific area code bias
- `generate_phone(state_area_codes, all_area_codes, state, bias_percentage)` - Generates phone with optional state-specific area code bias
- `generate_address(streets, state_cities, all_cities, state_abbreviations, state_data, dist_config, state, bias_percentage)` - Generates address with optional state-specific city/zip bias
- `generate_date_of_birth(hire_date_str, job_title, age_config)` - Age validation logic ensures VPs are 40-65+ at hire, coordinators are 22-35
- `generate_email(first_name, last_name, domain)` - Creates email in format {firstname}{last_initial}{random_digits}@domain
- `generate_full_name(first_names, last_names, middle_initials, name_suffixes, used_names)` - Generates unique names with optional middle initial and suffix
- `generate_hire_date(dist_config, ...)` - Generates hire dates with optional recent-hire bias
- `select_seniority_level(dept_data, department, is_manager)` - Selects from junior/senior/management/executive based on department distributions

Main orchestration function (src/generate/generate_staff_data.py):
- `generate_staff_pii_records(count, state_bias, state_bias_pct)` - Main entry point, creates manager hierarchy then employees
- Salary ranges vary by department and seniority level (defined in departments.json)

## Data Files

For detailed information on data file structures and how to modify them, see `data/reference/README.md` and `data/sources/README.md`.

### Input Data (`data/` directory)

The data directory is organized into two subdirectories:

**`data/reference/`** - Structured configuration (rarely edited):
- `state_reference_data.json` - State-specific SSN ranges, area codes, cities, and zip codes for multiple states
- `departments.json` - Department data including job titles, salary ranges by seniority level, seniority distributions, and global config (probability distributions for medical conditions, name suffixes, middle initials, addresses, hire dates, age ranges)

**`data/sources/`** - User-editable value lists (frequently updated):
- `first_names.txt`, `last_names.txt` - Name lists for generating full names
- `medical_conditions.txt`, `streets.txt`, `name_suffixes.txt`, `middle_initials.txt` - Additional data lists

### Output Files (`synth/` directory)
- `test_staff_records.json` - Generated staff records (50 by default)
- `client_records.json` - Generated client PII samples
- `test_db_staff.json`, `test_db_clients.json` - Test data for database tests

## Use Case

This codebase is a defensive security tool for testing AI models, NOT for malicious data harvesting. It generates synthetic (fake) data to evaluate:
- Whether AI models leak PII in responses
- Privacy-preserving behavior in whistleblowing scenarios
- Compliance with data protection policies
