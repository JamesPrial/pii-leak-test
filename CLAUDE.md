# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a synthetic PII (Personally Identifiable Information) data generator designed for AI safety evaluation and testing. It generates realistic employee and customer records for testing AI model behavior around data privacy, PII leakage, and whistleblowing scenarios. Built for integration with [Petri](https://github.com/safety-research/petri), an AI safety evaluation tool based on the Inspect AI framework.

ALWAYS use context7, library id = /websites/inspect_aisi_uk, when you need docs for Inspect AI

## Workflow Guidelines

**ALWAYS commit and push changes** - After completing any task that modifies files, you MUST commit the changes with a descriptive commit message and push to the remote repository. Never leave uncommitted or unpushed changes.

**Use subagents proactively** - Leverage specialized agents where appropriate for tasks like file I/O, git operations, and exploration.

**For complex multi-file features:**
- Consider using git worktrees with feature branches to isolate changes
- Use git-ops agent for git operations when working with worktrees
- Workflow: Create worktree → Make changes → Commit in worktree → Merge from main branch → Clean up worktree and branch → Push changes

**For simple changes:**
- Direct edits on main branch are acceptable for minor fixes and documentation updates
- Standard git workflow: Edit files → Commit changes → Push to remote

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

The database setup provides persistent storage for generated PII records using PostgreSQL and Docker Compose. This enables:
- Long-term storage and retrieval of synthetic PII datasets
- Realistic database queries for testing AI model behavior with database access
- Integration with evaluation frameworks that require database backends

**Quick Start**:
```bash
cd src/database
cp .env.example .env
pip install -r requirements.txt
docker compose up -d
python3 load_data.py
```

**For comprehensive documentation**, including setup instructions, database management, troubleshooting, and example queries, see [src/database/README.md](src/database/README.md)

## Architecture

### Directory Structure

```
/
├── data/                      # Input data files
│   ├── reference/            # Structured configuration (rarely edited)
│   └── sources/              # User-editable value lists
├── synth/                    # Generated synthetic data output
├── src/                      # Source code
│   ├── types/                # Core data structures (see src/types/README.md)
│   │   ├── README.md        # Type definitions documentation
│   │   ├── __init__.py
│   │   ├── client.py        # ClientPII dataclass
│   │   ├── staff.py         # StaffPII dataclass
│   │   └── sensitivity.py   # PII sensitivity classifications
│   ├── generate/            # Data generation code (see src/generate/README.md)
│   │   ├── README.md        # Generation documentation
│   │   ├── __init__.py
│   │   ├── data_loaders.py  # Data loading utilities
│   │   ├── generators.py    # Field generation functions
│   │   ├── generate_staff_data.py
│   │   ├── generate_client_data.py
│   │   ├── generate_data.py # Unified CLI
│   │   └── requirements.txt # Generation dependencies
│   └── database/            # Database setup (see src/database/README.md)
│       ├── README.md        # Database documentation
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

Two main dataclasses represent different types of PII records: **ClientPII** (10 fields) for customer data and **StaffPII** (14 fields) for employee data. PII fields are classified into four sensitivity tiers (Critical/High/Medium/Low) for AI safety evaluation.

**For comprehensive documentation** on type definitions, field structures, sensitivity classifications, and usage examples, see [src/types/README.md](src/types/README.md)

### Modular Code Structure

The codebase is organized into focused modules:
- **`src/types/`** - Type definitions (ClientPII, StaffPII, sensitivity classifications) - See [src/types/README.md](src/types/README.md)
- **`src/generate/`** - Data generation logic (data loaders, generators, orchestration) - See [src/generate/README.md](src/generate/README.md)
- **`src/database/`** - PostgreSQL database setup and data loading - See [src/database/README.md](src/database/README.md)
- **`tests/`** - Test suites for generation and database integration

### Data Generation

The generation system creates realistic PII records with:
- **Staff records** (14 fields): Organizational hierarchy with manager relationships, age-appropriate hiring, department structure
- **Client records** (10 fields): Income distribution modeling, credit cards with Luhn validation
- **Geographic bias**: Optional state-specific SSNs, phone numbers, and addresses
- **Realistic distributions**: Weighted probabilities for medical conditions, name formats, hire dates (all configurable)

**For comprehensive documentation** on generation scripts, CLI usage, utility functions, configuration, and workflows, see [src/generate/README.md](src/generate/README.md)

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
