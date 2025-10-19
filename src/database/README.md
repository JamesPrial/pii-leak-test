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
