# Data Generation

Synthetic PII (Personally Identifiable Information) data generators for creating realistic employee and customer records. Supports customizable record counts, geographic bias, organizational hierarchies, and realistic probability distributions.

## Overview

The generation system provides:
- **Realistic PII records** - Age-appropriate, geographically consistent data with valid formats
- **Organizational structure** - Hierarchical manager relationships for staff records
- **Geographic bias** - State-specific SSNs, phone numbers, and addresses
- **Configurable distributions** - Weighted probabilities for medical conditions, name formats, hire dates
- **Modular architecture** - Reusable generation functions and data loaders

## Quick Start

Generate 50 staff records (default):
```bash
cd src/generate
python3 generate_staff_data.py
```

Generate 100 client records:
```bash
python3 generate_client_data.py --count 100 --output-file ../../synth/my_clients.json
```

Generate with geographic bias (30% California residents):
```bash
python3 generate_staff_data.py --state-bias "California" --state-bias-pct 0.3
```

Use unified CLI for both types:
```bash
# From project root
python3 -m src.generate.generate_data staff -c 100 --state "Texas" --bias 0.5
python3 -m src.generate.generate_data both --staff-count 50 --client-count 100
```

## Files

| File | Type | Purpose |
|------|------|---------|
| `__init__.py` | Module init | Exports `generate_staff_pii_records` and `generate_client_pii_records` |
| `requirements.txt` | Dependencies | Lists pytest>=7.0.0, faker>=18.0.0 |
| `data_loaders.py` | Utility module | Functions to load and parse external data files |
| `generators.py` | Utility module | Core field generation functions (SSN, phone, email, address, DOB, etc.) |
| `generate_staff_data.py` | Main script | Generates staff/employee PII records (14 fields, manager hierarchy) |
| `generate_client_data.py` | Main script | Generates client/customer PII records (10 fields) |
| `generate_data.py` | CLI wrapper | Unified command-line interface with subcommands (staff/client/both) |

## Main Scripts

### generate_staff_data.py

Generates employee records with organizational hierarchy.

**Features:**
- **Manager hierarchy** - First 10% of records are managers (minimum 1)
- **Age-appropriate hiring** - DOB calculated based on job level and hire date
- **Department structure** - Job titles and salaries vary by department and seniority
- **Banking details** - Bank account and routing numbers included

**StaffPII Fields (14 total):**
- Identity: employee_id (UUID), name, ssn
- Contact: email, phone, address
- Employment: department, job_title, hire_date, manager, salary
- Financial: bank_account_number, routing_number
- Health: medical_condition (60% null)
- Personal: date_of_birth

**CLI Arguments:**
```bash
-c, --count          Number of records (default: 50)
-o, --output-file    Output path (default: ../../synth/test_staff_records.json)
```

**Usage:**
```bash
# Generate 50 records (default)
python3 generate_staff_data.py

# Generate 100 records with custom output
python3 generate_staff_data.py -c 100 -o ../../synth/my_staff.json
```

**Main Functions:**
- `generate_staff_pii_records(count, state_bias, state_bias_pct)` - Primary entry point
- `create_staff_record(...)` - Creates single StaffPII record with all 14 fields

### generate_client_data.py

Generates customer records with income distribution modeling.

**Features:**
- **Income distribution** - 30% low ($20k-45k), 50% middle ($45k-120k), 20% high ($120k-250k)
- **Credit cards** - Realistic 16-digit numbers with Luhn checksum validation
- **No hierarchy** - Independent records without manager relationships

**ClientPII Fields (10 total):**
- Identity: record_id (UUID), name, ssn
- Contact: email, phone, address
- Financial: salary, credit_card
- Health: medical_condition
- Personal: date_of_birth

**CLI Arguments:**
```bash
-c, --count          Number of records (default: 50)
-o, --output-file    Output path (default: ../../synth/client_records.json)
```

**Usage:**
```bash
# Generate 50 records (default)
python3 generate_client_data.py

# Generate 200 records with custom output
python3 generate_client_data.py -c 200 -o ../../synth/my_clients.json
```

**Main Functions:**
- `generate_client_pii_records(count, state_bias, state_bias_pct)` - Primary entry point
- `create_client_record(...)` - Creates single ClientPII record with all 10 fields

### generate_data.py

Unified CLI wrapper with subcommands for generating staff, client, or both record types.

**Subcommands:**

**1. `staff` - Generate staff records**
```bash
python3 -m src.generate.generate_data staff [OPTIONS]

Options:
  -c, --count INT      Number of staff records (default: 50)
  -o, --output PATH    Output file path (default: synth/test_staff_records.json)
  -s, --state TEXT     State name for geographic bias (e.g., "California")
  -b, --bias FLOAT     Bias percentage 0.0-1.0 (default: 0.1 = 10%)
```

**2. `client` - Generate client records**
```bash
python3 -m src.generate.generate_data client [OPTIONS]

Options:
  -c, --count INT      Number of client records (default: 50)
  -o, --output PATH    Output file path (default: synth/client_records.json)
  -s, --state TEXT     State name for geographic bias
  -b, --bias FLOAT     Bias percentage 0.0-1.0
```

**3. `both` - Generate both staff and client records**
```bash
python3 -m src.generate.generate_data both [OPTIONS]

Options:
  --staff-count INT     Number of staff records (default: 50)
  --staff-output PATH   Staff output file
  --client-count INT    Number of client records (default: 50)
  --client-output PATH  Client output file
  -s, --state TEXT      State name for geographic bias
  -b, --bias FLOAT      Bias percentage 0.0-1.0
```

**Usage Examples:**
```bash
# Generate 100 staff with California bias
python3 -m src.generate.generate_data staff -c 100 --state "California" --bias 0.3

# Generate 50 clients
python3 -m src.generate.generate_data client -c 50 -o synth/my_clients.json

# Generate both types with Texas bias
python3 -m src.generate.generate_data both --staff-count 100 --client-count 200 -s "Texas" -b 0.5
```

## Utility Modules

### data_loaders.py

Functions to load external data files and build lookup tables.

**Key Functions:**

**1. `load_state_data(data_dir)`**
Loads state reference data and builds lookup tables.
```python
Returns:
  {
    "state_data": dict,           # Full state reference data
    "state_ssn_ranges": dict,     # SSN area code ranges by state
    "state_abbreviations": dict,  # State name → abbreviation mapping
    "state_area_codes": dict,     # Phone area codes by state
    "state_cities": dict,         # Cities and zip codes by state
    "all_area_codes": list,       # All area codes (nationwide)
    "all_cities": list            # All cities (nationwide)
  }
```

**2. `load_department_data(data_dir)`**
Loads department configuration from departments.json.
```python
Returns:
  (dept_data, global_config)

  dept_data: {
    "Engineering": {
      "job_titles": {...},
      "salary_ranges": {...},
      "seniority_distribution": {...}
    },
    ...
  }

  global_config: {
    "medical_conditions": {"none_weight": 8, "condition_weight": 1},
    "name_suffixes": {"none_weight": 8, "suffix_weight": 1},
    "middle_initials": {"none_weight": 4, "initial_weight": 1},
    "address": {"apartment_probability": 0.3},
    "hire_date": {...},
    "age_ranges": {...}
  }
```

**3. `load_names_and_conditions(data_dir, dist_config)`**
Loads names and medical conditions with weighted distributions.
```python
Returns:
  {
    "first_names": list,
    "last_names": list,
    "medical_conditions": list,  # Weighted: 60% "None", 40% conditions
    "name_suffixes": list,       # Weighted: ~67% "", ~33% suffixes
    "middle_initials": list      # Weighted: ~18% "", ~82% initials
  }
```

**4. `load_streets(data_dir)`**
Loads street names from data/sources/streets.txt.
```python
Returns: list  # ["Main St", "Oak Ave", "Elm Rd", ...]
```

### generators.py

Core field generation functions for individual PII fields.

**Identity & Contact:**

- **`generate_ssn(state_ssn_ranges, state, bias_percentage=0.1)`**
  - Generates 9-digit SSN with optional state-specific area code bias
  - Format: "123-45-6789"
  - When `random() < bias_percentage`, uses state SSN ranges

- **`generate_phone(state_area_codes, all_area_codes, state, bias_percentage=0.1)`**
  - Generates 10-digit phone number with state bias
  - Format: "201-555-0123"
  - When `random() < bias_percentage`, uses state area codes

- **`generate_email(first_name, last_name, employee_id, domain)`**
  - Staff email: `{firstname}{last_initial}{uuid_suffix}@domain`
  - Example: "johns123@company.com"

- **`generate_client_email(first_name, last_name)`**
  - Client email with random public domains (gmail, yahoo, outlook, etc.)
  - Example: "john.doe@gmail.com"

- **`generate_full_name(first_names, last_names, middle_initials, name_suffixes, used_names)`**
  - Generates unique full names with optional middle initial and suffix
  - Tracks `used_names` set to ensure uniqueness
  - Examples: "John M. Doe Jr.", "Jane Smith"

**Address & Location:**

- **`generate_address(streets, state_cities, all_cities, state_abbreviations, state_data, dist_config, state, bias_percentage)`**
  - Generates full address with optional apartment/suite number (30% probability)
  - Uses state bias for city/zip selection
  - Format: "123 Main St Apt 2B, Newark, NJ 07102"

- **`get_state_abbreviation(state_abbreviations, state)`**
  - Helper to convert state name → abbreviation
  - Example: "New Jersey" → "NJ"

**Financial:**

- **`generate_bank_account()`**
  - Generates 16-digit bank account number
  - Format: "1234567890123456"

- **`generate_routing_number()`**
  - Generates 9-digit routing number
  - Format: "021000021"

- **`generate_credit_card()`**
  - Generates 16-digit credit card with Luhn checksum validation
  - Supports Visa (4xxx), Mastercard (5xxx), Discover (6xxx)
  - Format: "4532-1234-5678-9010"

- **`generate_client_salary()`**
  - Income distribution with 3 tiers:
    - 30% low: $20,000 - $45,000
    - 50% middle: $45,000 - $120,000
    - 20% high: $120,000 - $250,000

**Temporal:**

- **`generate_hire_date(dist_config, start_year, end_year, recent_bias)`**
  - Generates hire date with optional recent-hire bias
  - Uses exponential weighting when `recent_bias=True`
  - Format: "YYYY-MM-DD"

- **`generate_date_of_birth(hire_date_str, job_title, age_config)`**
  - Age-appropriate DOB based on job level and hire date
  - Age ranges from `age_config` in departments.json:
    - Junior (coordinator, analyst): 22-35 at hire
    - Senior (engineer, manager): 28-50 at hire
    - Management (director, VP): 35-55 at hire
    - Executive (C-level, VP): 40-65 at hire
  - Format: "YYYY-MM-DD"

- **`generate_client_dob()`**
  - Client DOB for ages 18-90 with bias toward 25-65
  - Format: "YYYY-MM-DD"

**Employment:**

- **`select_seniority_level(dept_data, department, is_manager)`**
  - Selects seniority level based on department distributions
  - Levels: junior, senior, management, executive
  - Example: Engineering might have 40% junior, 40% senior, 15% management, 5% executive

- **`generate_employee_details(department, seniority_level, is_manager, dist_config, dept_data, medical_conditions)`**
  - Helper function combining hire date, DOB, salary, medical condition
  - Uses department-specific salary ranges for selected seniority level

## CLI Usage Examples

### Direct Script Execution

**Basic usage:**
```bash
cd src/generate

# Generate 50 staff records (default)
python3 generate_staff_data.py

# Generate 100 staff records
python3 generate_staff_data.py --count 100

# Custom output file
python3 generate_staff_data.py -c 50 -o ../../synth/my_staff.json

# Generate 200 client records
python3 generate_client_data.py --count 200 --output-file ../../synth/clients_200.json
```

**Geographic bias:**
```bash
# 30% California residents
python3 generate_staff_data.py --state-bias "California" --state-bias-pct 0.3

# 50% Texas residents
python3 generate_client_data.py --state-bias "Texas" --state-bias-pct 0.5
```

### Unified CLI (from project root)

**Staff generation:**
```bash
# Basic
python3 -m src.generate.generate_data staff

# With options
python3 -m src.generate.generate_data staff -c 100 -o synth/staff_100.json

# With geographic bias
python3 -m src.generate.generate_data staff -c 200 --state "California" --bias 0.4
```

**Client generation:**
```bash
# Basic
python3 -m src.generate.generate_data client

# With options
python3 -m src.generate.generate_data client -c 150 -o synth/clients_150.json

# With geographic bias
python3 -m src.generate.generate_data client -c 100 --state "New York" --bias 0.6
```

**Both types:**
```bash
# Default counts (50 each)
python3 -m src.generate.generate_data both

# Custom counts
python3 -m src.generate.generate_data both --staff-count 100 --client-count 200

# With geographic bias and custom outputs
python3 -m src.generate.generate_data both \
  --staff-count 150 \
  --staff-output synth/staff_150.json \
  --client-count 300 \
  --client-output synth/clients_300.json \
  --state "Florida" \
  --bias 0.3
```

### Programmatic Usage

```python
from src.generate import generate_staff_pii_records, generate_client_pii_records

# Generate 100 staff records with California bias
staff_records = generate_staff_pii_records(
    count=100,
    state_bias="California",
    state_bias_pct=0.3
)

# Generate 200 client records with Texas bias
client_records = generate_client_pii_records(
    count=200,
    state_bias="Texas",
    state_bias_pct=0.5
)

# Access individual records
for record in staff_records:
    print(record.to_dict())
```

## Configuration & Data Files

### Input Data Files

**Reference data (data/reference/):**
- **`state_reference_data.json`** - State-specific data for multiple states
  - SSN area code ranges (e.g., NJ: 001-134)
  - Phone area codes (e.g., NJ: [201, 551, 609, 732, 848, 856, 862, 908, 973])
  - Cities with zip codes
  - State abbreviations

- **`departments.json`** - Department configuration and global distributions
  - Department names: Engineering, Sales, Marketing, HR, Finance, Operations, IT
  - Job titles by department and seniority level
  - Salary ranges by department and seniority
  - Seniority distributions (% junior/senior/management/executive)
  - **`global_config` key** contains:
    - `medical_conditions`: Weight ratios (none_weight: 8, condition_weight: 1) → 60% null
    - `name_suffixes`: Weight ratios (none_weight: 8, suffix_weight: 1) → ~67% no suffix
    - `middle_initials`: Weight ratios (none_weight: 4, initial_weight: 1) → ~18% no initial
    - `address`: apartment_probability (0.3) → 30% include apt/suite
    - `hire_date`: default_start_year, default_end_year, recent_hire_bias
    - `age_ranges`: Age ranges by seniority level for DOB calculation

**Source data (data/sources/):**
- `first_names.txt` - First names (one per line)
- `last_names.txt` - Last names (one per line)
- `medical_conditions.txt` - Health conditions (one per line, weighted distribution)
- `streets.txt` - Street names (one per line)
- `name_suffixes.txt` - Name suffixes: Jr., Sr., II, III, IV
- `middle_initials.txt` - Middle initials: A-Z

### Output Files

**Default output directory: `synth/`**
- `test_staff_records.json` - Staff records (50 by default)
- `client_records.json` - Client records (50 by default)
- `test_db_staff.json` - Test data for database tests
- `test_db_clients.json` - Test data for database tests

### Distribution Configuration

All probability distributions are configurable via `global_config` in `departments.json`:

**Medical conditions (60% null):**
```json
"medical_conditions": {
  "none_weight": 8,
  "condition_weight": 1
}
```

**Name suffixes (~67% no suffix):**
```json
"name_suffixes": {
  "none_weight": 8,
  "suffix_weight": 1
}
```

**Middle initials (~18% no initial):**
```json
"middle_initials": {
  "none_weight": 4,
  "initial_weight": 1
}
```

**Addresses (30% include apt/suite):**
```json
"address": {
  "apartment_probability": 0.3
}
```

**Hire dates:**
```json
"hire_date": {
  "default_start_year": 2010,
  "default_end_year": 2024,
  "recent_hire_bias": true
}
```

**Age ranges by seniority:**
```json
"age_ranges": {
  "junior": {"min": 22, "max": 35},
  "senior": {"min": 28, "max": 50},
  "management": {"min": 35, "max": 55},
  "executive": {"min": 40, "max": 65}
}
```

## Workflows

### Staff Record Generation Flow

1. **Load Data Files**
   - State data (SSN ranges, area codes, cities/zips)
   - Department data (job titles, salary ranges, distributions)
   - Names, medical conditions, streets

2. **Generate Managers**
   - Calculate manager count: `max(1, count // 10)` (10% or minimum 1)
   - Create manager records with `manager=None`
   - Assign executive/management job titles

3. **Generate Employees**
   - Create remaining records
   - Randomly assign managers from manager pool
   - Assign job titles based on seniority distributions
   - Calculate age-appropriate DOBs based on hire date and job level

4. **Shuffle & Serialize**
   - Shuffle records to avoid sequential ordering (managers no longer first)
   - Convert to dictionaries via `to_dict()`
   - Write to JSON file

### Client Record Generation Flow

1. **Load Data Files**
   - State data (SSN ranges, area codes, cities/zips)
   - Names, medical conditions, streets
   - Department config for distributions (medical conditions, name formats)

2. **Generate Client Records**
   - Create records with income distribution (30% low, 50% mid, 20% high)
   - Generate credit cards with Luhn checksum validation
   - Use public email domains (gmail, yahoo, outlook, etc.)
   - No manager relationships or organizational hierarchy

3. **Shuffle & Serialize**
   - Shuffle records
   - Convert to dictionaries via `to_dict()`
   - Write to JSON file

### Geographic Bias Feature

When `state_bias` and `state_bias_pct` are provided:

1. **Bias Threshold Check** - For each field, generate `random()`
2. **If `random() < bias_percentage`** - Use state-specific data:
   - SSN: Use state SSN area code ranges
   - Phone: Use state area codes
   - Address: Use state cities and zip codes
3. **Otherwise** - Use nationwide data:
   - SSN: Use all SSN ranges
   - Phone: Use all area codes
   - Address: Use all cities and states

**Example:** With `state_bias="California"` and `bias_percentage=0.3`:
- 30% of records will have California SSNs, phone numbers, and addresses
- 70% of records will have randomly distributed nationwide data

## Dependencies

**requirements.txt:**
```
pytest>=7.0.0   # Testing framework
faker>=18.0.0   # Fake data generation library (imported but currently using built-in random)
```

**Install:**
```bash
cd src/generate
pip install -r requirements.txt
```

## Testing

Run generation tests:
```bash
# All tests
pytest tests/generate/test_generate_staff.py
pytest tests/generate/test_generate_client.py

# Verbose output
pytest tests/generate/test_generate_staff.py -v

# Specific test
pytest tests/generate/test_generate_staff.py::TestGenerators::test_generate_ssn
```

## Design Patterns

1. **Modular Architecture**
   - `data_loaders.py`: File I/O and data structure building
   - `generators.py`: Individual field generation functions
   - `generate_staff_data.py`: Staff orchestration with hierarchy
   - `generate_client_data.py`: Client orchestration with income distribution
   - `generate_data.py`: Unified CLI interface

2. **Weighted Distributions**
   - Medical conditions: 60% null (8:1 weight ratio)
   - Name suffixes: ~67% no suffix (8:1 weight ratio)
   - Middle initials: ~18% no initial (4:1 weight ratio)
   - Client income: 30% low, 50% mid, 20% high (tiered probabilities)

3. **Uniqueness & Realism**
   - Tracks `used_names` set to ensure unique full names
   - UUID for employee_id and record_id (non-sequential)
   - Age-appropriate DOB based on job title and hire date
   - Manager-first creation ensures valid manager references
   - Luhn checksum validation for credit cards

4. **Flexible Configuration**
   - All distributions defined in JSON data files
   - CLI supports custom counts, output paths, and geographic bias
   - Importable functions allow programmatic use
   - Easy to extend with new states or departments

## Documentation

For comprehensive documentation:
- **[../../CLAUDE.md](../../CLAUDE.md)** - Overall architecture and workflow guidelines
- **[../types/README.md](../types/README.md)** - ClientPII and StaffPII dataclass definitions
- **[../database/README.md](../database/README.md)** - Database setup and data loading
- **[../../data/reference/README.md](../../data/reference/README.md)** - Reference data formats
- **[../../data/sources/README.md](../../data/sources/README.md)** - Editable source data lists
