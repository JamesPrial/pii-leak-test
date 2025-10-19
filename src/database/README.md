# Database Setup

PostgreSQL database setup for storing and querying synthetic PII records. Provides persistent storage for generated staff and client data using Docker Compose.

## Quick Start

1. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env to customize credentials (optional)
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start PostgreSQL**:
   ```bash
   docker compose up -d
   ```

4. **Load data**:
   ```bash
   python3 load_data.py
   ```

## CRUD API

### Overview

The database module provides a clean, high-level Python API for working with synthetic PII records. The `Database` class offers type-safe CRUD operations through repository objects (`StaffRepository` and `ClientRepository`), with automatic transaction management and connection handling.

Key features:
- Type-safe operations using `StaffPII` and `ClientPII` dataclasses
- Context manager pattern for automatic connection management
- Transaction safety (auto-commit on success, auto-rollback on error)
- Rich query capabilities (filtering, search, hierarchy queries)
- Comprehensive error handling

### Basic Usage

**Import and connect**:
```python
from src.database import Database
from src.types.staff import StaffPII
from src.types.client import ClientPII

# Use context manager for automatic connection handling
with Database() as db:
    # All database operations go here
    pass
```

**Create records**:
```python
with Database() as db:
    # Create a staff record
    employee = StaffPII(
        employee_id="emp-001",
        name="Alice Johnson",
        email="alice@example.com",
        phone="555-1234",
        address="123 Main St",
        date_of_birth="1990-05-15",
        ssn="123-45-6789",
        department="Engineering",
        job_title="Senior Engineer",
        hire_date="2020-01-15",
        manager=None,
        salary=120000,
        bank_account_number="1234567890",
        routing_number="123456789",
        medical_condition="None"
    )
    db.staff.create(employee)

    # Create a client record
    client = ClientPII(
        record_id="client-001",
        name="Bob Smith",
        email="bob@example.com",
        phone="555-5678",
        address="456 Oak Ave",
        date_of_birth="1985-08-20",
        salary=75000,
        medical_condition="Asthma",
        ssn="987-65-4321",
        credit_card="4532-1234-5678-9012"
    )
    db.clients.create(client)
```

**Read records**:
```python
with Database() as db:
    # Get by ID
    employee = db.staff.get_by_id("emp-001")
    client = db.clients.get_by_id("client-001")

    # Get all records
    all_staff = db.staff.get_all()
    all_clients = db.clients.get_all()

    # Get with limit
    first_10_staff = db.staff.get_all(limit=10)
```

**Update records**:
```python
with Database() as db:
    # Fetch record
    employee = db.staff.get_by_id("emp-001")

    # Modify fields
    employee.salary = 130000
    employee.job_title = "Lead Engineer"

    # Save changes
    db.staff.update(employee)
```

**Delete records**:
```python
with Database() as db:
    # Delete by ID
    db.staff.delete("emp-001")
    db.clients.delete("client-001")
```

### Available Methods

**StaffRepository Methods**:
- `create(staff: StaffPII) -> None` - Insert a new staff record
- `get_by_id(employee_id: str) -> Optional[StaffPII]` - Fetch by employee ID
- `get_all(limit: Optional[int] = None) -> List[StaffPII]` - Fetch all staff records
- `update(staff: StaffPII) -> None` - Update an existing staff record
- `delete(employee_id: str) -> None` - Delete a staff record
- `filter(**kwargs) -> List[StaffPII]` - Filter records by field values
- `search_by_email(email: str) -> Optional[StaffPII]` - Find by email address
- `search_by_ssn(ssn: str) -> Optional[StaffPII]` - Find by SSN
- `get_by_department(department: str) -> List[StaffPII]` - Filter by department
- `get_direct_reports(manager_id: str) -> List[StaffPII]` - Get employees reporting to a manager
- `get_managers() -> List[StaffPII]` - Get all managers (employees with no manager)

**ClientRepository Methods**:
- `create(client: ClientPII) -> None` - Insert a new client record
- `get_by_id(record_id: str) -> Optional[ClientPII]` - Fetch by record ID
- `get_all(limit: Optional[int] = None) -> List[ClientPII]` - Fetch all client records
- `update(client: ClientPII) -> None` - Update an existing client record
- `delete(record_id: str) -> None` - Delete a client record
- `filter(**kwargs) -> List[ClientPII]` - Filter records by field values
- `search_by_email(email: str) -> Optional[ClientPII]` - Find by email address
- `search_by_ssn(ssn: str) -> Optional[ClientPII]` - Find by SSN

### Filtering and Search

**Filter by field values**:
```python
with Database() as db:
    # Filter staff by department
    engineers = db.staff.filter(department="Engineering")

    # Filter by multiple criteria
    senior_engineers = db.staff.filter(
        department="Engineering",
        job_title="Senior Engineer"
    )

    # Filter clients by income range (requires custom SQL)
    # Use get_all() and filter in Python for complex queries
    high_income = [c for c in db.clients.get_all() if c.salary > 100000]
```

**Search by unique fields**:
```python
with Database() as db:
    # Find staff by email
    employee = db.staff.search_by_email("alice@example.com")

    # Find staff by SSN
    employee = db.staff.search_by_ssn("123-45-6789")

    # Find client by email
    client = db.clients.search_by_email("bob@example.com")

    # Find client by SSN
    client = db.clients.search_by_ssn("987-65-4321")
```

**Get by department**:
```python
with Database() as db:
    # Get all employees in a department
    engineering_staff = db.staff.get_by_department("Engineering")
    marketing_staff = db.staff.get_by_department("Marketing")
```

### Manager Hierarchy Queries

The staff repository provides specialized methods for working with organizational hierarchies:

**Get direct reports**:
```python
with Database() as db:
    # Get all employees who report to a specific manager
    manager_id = "emp-001"
    reports = db.staff.get_direct_reports(manager_id)

    print(f"Manager {manager_id} has {len(reports)} direct reports:")
    for employee in reports:
        print(f"  - {employee.name} ({employee.job_title})")
```

**Get all managers**:
```python
with Database() as db:
    # Get all managers (employees with manager=None)
    managers = db.staff.get_managers()

    print(f"Found {len(managers)} managers:")
    for manager in managers:
        reports = db.staff.get_direct_reports(manager.employee_id)
        print(f"  - {manager.name}: {len(reports)} direct reports")
```

**Build org chart**:
```python
with Database() as db:
    # Build a complete organizational hierarchy
    def print_org_chart(manager_id=None, indent=0):
        if manager_id is None:
            # Start with top-level managers
            employees = db.staff.get_managers()
        else:
            # Get direct reports for this manager
            employees = db.staff.get_direct_reports(manager_id)

        for emp in employees:
            print("  " * indent + f"- {emp.name} ({emp.job_title})")
            # Recursively print their reports
            print_org_chart(emp.employee_id, indent + 1)

    print("Organization Chart:")
    print_org_chart()
```

### Transaction Safety

The `Database` class uses context managers to ensure proper transaction handling:

**Automatic commit on success**:
```python
with Database() as db:
    # All operations within this block are part of one transaction
    employee = db.staff.get_by_id("emp-001")
    employee.salary = 130000
    db.staff.update(employee)

    client = db.clients.get_by_id("client-001")
    client.salary = 80000
    db.clients.update(client)

    # Transaction automatically commits when exiting without error
```

**Automatic rollback on error**:
```python
try:
    with Database() as db:
        employee = db.staff.get_by_id("emp-001")
        employee.salary = 130000
        db.staff.update(employee)

        # This raises an error
        invalid_employee = db.staff.get_by_id("invalid-id")
        invalid_employee.salary = 999999
        db.staff.update(invalid_employee)

except Exception as e:
    # Transaction automatically rolled back
    # No changes were saved to the database
    print(f"Error: {e}")
```

**Manual error handling**:
```python
with Database() as db:
    try:
        employee = db.staff.get_by_id("emp-001")
        if employee is None:
            print("Employee not found")
        else:
            employee.salary = 130000
            db.staff.update(employee)
    except Exception as e:
        print(f"Update failed: {e}")
        # Transaction will still rollback on exit
```

### Error Handling

**Common exceptions and how to handle them**:

**Record not found**:
```python
with Database() as db:
    employee = db.staff.get_by_id("nonexistent-id")
    if employee is None:
        print("Employee not found")
    else:
        # Work with employee
        pass
```

**Duplicate key violation**:
```python
from psycopg2 import IntegrityError

with Database() as db:
    try:
        # Attempt to create employee with duplicate ID
        employee = StaffPII(employee_id="emp-001", ...)
        db.staff.create(employee)
    except IntegrityError as e:
        print(f"Employee ID already exists: {e}")
```

**Foreign key violation (invalid manager)**:
```python
from psycopg2 import IntegrityError

with Database() as db:
    try:
        # Attempt to create employee with invalid manager ID
        employee = StaffPII(
            employee_id="emp-002",
            manager="invalid-manager-id",  # This manager doesn't exist
            ...
        )
        db.staff.create(employee)
    except IntegrityError as e:
        print(f"Invalid manager ID: {e}")
```

**Connection errors**:
```python
from psycopg2 import OperationalError

try:
    with Database() as db:
        # Database operations
        pass
except OperationalError as e:
    print(f"Database connection failed: {e}")
    print("Ensure Docker container is running: docker compose up -d")
```

**General error handling pattern**:
```python
from psycopg2 import Error as Psycopg2Error

try:
    with Database() as db:
        # Perform database operations
        employee = db.staff.get_by_id("emp-001")
        employee.salary = 130000
        db.staff.update(employee)

except Psycopg2Error as e:
    print(f"Database error: {e}")
    # Handle database-specific errors

except Exception as e:
    print(f"Unexpected error: {e}")
    # Handle other errors
```

## Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | PostgreSQL service definition with health checks and persistent storage |
| `init_schema.sql` | Database schema defining `staff` and `clients` tables with constraints |
| `load_data.py` | Script to load JSON records into the database |
| `queries.sql` | Example SQL queries demonstrating data access patterns |
| `requirements.txt` | Python dependencies (psycopg2-binary, python-dotenv, pytest) |
| `.env.example` | Environment configuration template with default values |

## Common Commands

**Start database**:
```bash
docker compose up -d
```

**Stop database** (preserves data):
```bash
docker compose down
```

**Stop and remove all data** (destructive):
```bash
docker compose down -v
```

**Load data with custom files**:
```bash
python3 load_data.py --staff-file /path/to/staff.json --client-file /path/to/clients.json
```

**Access psql shell**:
```bash
docker compose exec postgres psql -U pii_admin -d pii_test_data
```

**Run example queries**:
```bash
docker compose exec postgres psql -U pii_admin -d pii_test_data -f /docker-entrypoint-initdb.d/queries.sql
```

**View logs**:
```bash
docker compose logs -f postgres
```

**Run database tests**:
```bash
pytest ../../tests/database/test_database.py -v
```

## Database Schema

The database contains two main tables:

**staff** - Employee records (14 PII fields):
- Identity: employee_id (PK), first_name, last_name, ssn (unique)
- Contact: email (unique), phone, address, city, state, zip
- Employment: department, job_title, hire_date, salary, manager_id (FK)
- Medical: medical_condition

**clients** - Customer records (10 PII fields):
- Identity: client_id (PK), first_name, last_name, ssn (unique)
- Contact: email (unique), phone, address, city, state, zip
- Financial: income

Both tables include indexes on email and SSN for efficient queries.

## Troubleshooting

**Connection refused**:
- Verify Docker is running: `docker ps`
- Check container health: `docker compose ps`
- Review logs: `docker compose logs postgres`

**Port conflicts** (5432 in use):
- Change `POSTGRES_PORT` in `.env` to use a different port
- Update connection strings accordingly

**Foreign key violations** (manager_id):
- Ensure staff data has valid manager relationships
- First 10% of staff records should be managers with `manager_id=null`

## Documentation

For comprehensive documentation including:
- Detailed setup instructions
- Data loading options and flags
- Database management workflows
- Backup/restore procedures
- Advanced troubleshooting

See the **PostgreSQL Database Setup** section in [../../CLAUDE.md](../../CLAUDE.md#postgresql-database-setup)
