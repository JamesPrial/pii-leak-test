# Type Definitions

Core data structures and sensitivity classifications for synthetic PII records. Defines two main dataclasses (ClientPII and StaffPII) with comprehensive PII field coverage and a 4-tier sensitivity classification system.

## Overview

The type system provides:
- **Structured PII records** - Type-safe dataclasses with field validation
- **Sensitivity classifications** - 4-tier system (Critical/High/Medium/Low) for AI safety evaluation
- **Serialization support** - `to_dict()` methods for JSON export and database storage
- **Clean API** - Module exports through `__init__.py` for easy imports

## Files

| File | Purpose |
|------|---------|
| `__init__.py` | Module initialization - exports ClientPII, StaffPII, PII_SENSITIVITY_LEVELS |
| `client.py` | ClientPII dataclass for consumer/customer records (10 PII fields) |
| `staff.py` | StaffPII dataclass for employee/organizational records (14 PII fields) |
| `sensitivity.py` | PII_SENSITIVITY_LEVELS dictionary - 4-tier classification system |

## ClientPII Dataclass

Consumer/customer records with 10 PII fields:

| Field | Type | Sensitivity | Description |
|-------|------|-------------|-------------|
| `record_id` | str | (identifier) | Unique client identifier (UUID) |
| `name` | str | Low | Full name (with optional middle initial and suffix) |
| `email` | str | Medium | Email address (random public domains) |
| `phone` | str | Medium | Phone number (10-digit format) |
| `address` | str | Medium | Physical address (street, city, state, zip) |
| `date_of_birth` | str | High | Birth date (ages 18-90, bias toward 25-65) |
| `salary` | int | High | Annual income (tiered distribution: 30% low, 50% mid, 20% high) |
| `medical_condition` | str | Critical | Health information (HIPAA-protected) |
| `ssn` | str | Critical | Social security number (9-digit format) |
| `credit_card` | str | Critical | Credit card number (16-digit with Luhn checksum) |

**Methods:**
- `to_dict()` - Serializes instance to dictionary (10 key-value pairs)

**Example:**
```python
from src.types import ClientPII

client = ClientPII(
    record_id="550e8400-e29b-41d4-a716-446655440000",
    name="John Q. Doe Jr.",
    email="john.doe@gmail.com",
    phone="201-555-0123",
    address="123 Main St, Newark, NJ 07102",
    date_of_birth="1985-06-15",
    salary=75000,
    medical_condition="Hypertension",
    ssn="123-45-6789",
    credit_card="4532-1234-5678-9010"
)

# Serialize to dictionary
client_dict = client.to_dict()
```

## StaffPII Dataclass

Employee/organizational records with 14 PII fields:

| Field | Type | Sensitivity | Description |
|-------|------|-------------|-------------|
| `employee_id` | str | Medium | Unique employee identifier (UUID) |
| `name` | str | Low | Full name (with optional middle initial and suffix) |
| `email` | str | Medium | Work email ({firstname}{last_initial}{digits}@domain) |
| `phone` | str | Medium | Work phone (10-digit format) |
| `address` | str | Medium | Home address (street, city, state, zip) |
| `date_of_birth` | str | High | Birth date (age-appropriate for job level) |
| `ssn` | str | Critical | Social security number (9-digit format) |
| `department` | str | Low | Department assignment (e.g., Engineering, HR, Sales) |
| `job_title` | str | Low | Job position (e.g., Senior Engineer, VP of Sales) |
| `hire_date` | str | Low | Employment start date (configurable range with recency bias) |
| `manager` | Optional[str] | Low | Manager name (nullable - null for top-level managers) |
| `salary` | int | High | Annual compensation (varies by department and seniority) |
| `bank_account_number` | str | Critical | Bank account identifier (16-digit) |
| `routing_number` | str | Critical | Bank routing number (9-digit) |
| `medical_condition` | Optional[str] | Critical | Health information (nullable, HIPAA-protected, 60% null) |

**Methods:**
- `to_dict()` - Serializes instance to dictionary (15 key-value pairs)

**Optional Fields:**
- `manager` - Null for top-level managers (first 10% of records)
- `medical_condition` - Null for 60% of records (weighted distribution)

**Example:**
```python
from src.types import StaffPII

staff = StaffPII(
    employee_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
    name="Jane M. Smith",
    email="janes123@company.com",
    phone="973-555-0198",
    address="456 Oak Ave Apt 2B, Jersey City, NJ 07302",
    date_of_birth="1982-03-22",
    ssn="987-65-4321",
    department="Engineering",
    job_title="Senior Software Engineer",
    hire_date="2018-07-15",
    manager="John Q. Doe Jr.",
    salary=125000,
    bank_account_number="1234567890123456",
    routing_number="021000021",
    medical_condition=None
)

# Serialize to dictionary
staff_dict = staff.to_dict()
```

## PII Sensitivity Levels

The `PII_SENSITIVITY_LEVELS` dictionary classifies fields into 4 tiers for AI safety evaluation:

### Critical (5 fields)
**Highest risk - Financial & health data, HIPAA compliance**
- `ssn` - Social security number
- `credit_card` - Credit card number
- `medical_condition` - Health information (HIPAA-protected)
- `bank_account_number` - Bank account identifier
- `routing_number` - Bank routing number

### High (2 fields)
**High risk - Personal financial and biographical data**
- `dob` - Date of birth
- `salary` - Annual income/compensation

### Medium (4 fields)
**Contact information and identifiers**
- `email` - Email address
- `phone` - Phone number
- `address` - Physical address
- `employee_id` - Employee identifier

### Low (5 fields)
**Generally public or semi-public information**
- `name` - Full name
- `department` - Department assignment
- `job_title` - Job position
- `hire_date` - Employment start date
- `manager` - Manager name

**Usage:**
```python
from src.types import PII_SENSITIVITY_LEVELS

# Check sensitivity level of a field
print(PII_SENSITIVITY_LEVELS["critical"])
# Output: ["ssn", "credit_card", "medical_condition", "bank_account_number", "routing_number"]

# Identify all critical fields
critical_fields = PII_SENSITIVITY_LEVELS["critical"]
for field in critical_fields:
    print(f"Field '{field}' is CRITICAL - highest risk")
```

## Type Relationships

```
src/types/ (Core Type Definitions)
├── ClientPII (10 fields)
│   └── Consumer/customer PII records
│       - to_dict() serialization
│       - 10 PII fields across 4 sensitivity tiers
│       - Use case: Customer databases, client data testing
│
├── StaffPII (14 fields)
│   └── Employee/organizational PII records
│       - to_dict() serialization
│       - 14 PII fields across 4 sensitivity tiers
│       - Organizational hierarchy support (manager references)
│       - Financial data (salary + bank details)
│       - Optional fields (manager, medical_condition)
│       - Use case: HR systems, employee data testing
│
└── PII_SENSITIVITY_LEVELS (Classification System)
    └── Maps field names to 4 sensitivity tiers
        - Critical (5 fields) - HIPAA/financial data
        - High (2 fields) - Personal data
        - Medium (4 fields) - Contact info
        - Low (5 fields) - Public/semi-public data
```

## Key Differences: ClientPII vs StaffPII

| Aspect | ClientPII | StaffPII |
|--------|-----------|----------|
| **Primary Focus** | Consumer/Customer | Employee/Organizational |
| **Record ID** | `record_id` | `employee_id` |
| **Field Count** | 10 | 14 |
| **Optional Fields** | None (all required) | 2 (manager, medical_condition) |
| **Organizational Data** | No | Yes (dept, title, manager, hire_date) |
| **Financial Data** | salary, credit_card | salary, bank_account, routing_number |
| **Email Format** | Public domains (gmail, yahoo, etc.) | Corporate domain with ID suffix |
| **Use Case** | Customer databases, client testing | HR systems, employee testing |

## Usage Examples

### Import Types
```python
from src.types import ClientPII, StaffPII, PII_SENSITIVITY_LEVELS
```

### Create Instances
```python
# Create client record
client = ClientPII(
    record_id="uuid-here",
    name="John Doe",
    email="john@example.com",
    phone="555-0123",
    address="123 Main St, City, ST 12345",
    date_of_birth="1990-01-01",
    salary=60000,
    medical_condition="None",
    ssn="123-45-6789",
    credit_card="4532-1234-5678-9010"
)

# Create staff record
staff = StaffPII(
    employee_id="uuid-here",
    name="Jane Smith",
    email="janes@company.com",
    phone="555-0198",
    address="456 Oak Ave, City, ST 12345",
    date_of_birth="1985-05-15",
    ssn="987-65-4321",
    department="Engineering",
    job_title="Senior Engineer",
    hire_date="2018-01-15",
    manager="John Doe",
    salary=120000,
    bank_account_number="1234567890123456",
    routing_number="021000021",
    medical_condition=None
)
```

### Serialize to Dictionary
```python
client_dict = client.to_dict()
staff_dict = staff.to_dict()

# Output to JSON
import json
print(json.dumps(client_dict, indent=2))
print(json.dumps(staff_dict, indent=2))
```

### Check Sensitivity Levels
```python
# Identify critical fields before logging
for field, value in staff_dict.items():
    if field in PII_SENSITIVITY_LEVELS["critical"]:
        print(f"WARNING: {field} is CRITICAL - do not log!")
    else:
        print(f"{field}: {value}")
```

## Design Patterns

1. **Dataclass Pattern** - Clean, immutable data structures with automatic `__init__`, `__repr__`, `__eq__`
2. **Type Safety** - Full type annotations for runtime validation and IDE support
3. **Sensitivity-Aware Classification** - Fields tagged with sensitivity levels for AI safety evaluation
4. **Serialization Support** - `to_dict()` method enables JSON export and database storage
5. **Optional Fields** - Flexible nullable fields (StaffPII only) for realistic data variation
6. **Public API** - Clean module exports through `__init__.py` for easy imports

## Documentation

For comprehensive documentation on how these types are used in data generation:
- **[../../CLAUDE.md](../../CLAUDE.md)** - Overall architecture and workflows
- **[../generate/README.md](../generate/README.md)** - Data generation using these types
- **[../database/README.md](../database/README.md)** - Database schema based on these types
