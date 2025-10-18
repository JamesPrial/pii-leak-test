# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a synthetic PII (Personally Identifiable Information) data generator designed for AI safety evaluation and testing. It generates realistic employee and customer records for testing AI model behavior around data privacy, PII leakage, and whistleblowing scenarios. Built for integration with [Petri](https://github.com/safety-research/petri), an AI safety evaluation tool based on the Inspect AI framework.

## CRITICAL Workflow Requirements

**ALWAYS follow this workflow:**

1. **Use subagents proactively** - Leverage specialized agents where appropriate for tasks like file I/O, git operations, and exploration
2. **Git worktree workflow** - Before beginning any file editing/creation:
   - **Create worktree**: Use git-ops agent to create a new worktree with a feature branch from main
   - **Make changes**: Edit/create files in the worktree directory
   - **Commit and cleanup**: Use ONE git-ops agent to handle all commit and cleanup steps:
     - Commit your changes in the worktree
     - Checkout main branch in the main worktree
     - Merge the feature branch into main
     - Remove the worktree directory
     - Delete the feature branch
   - **Important**: The merge must happen from the main worktree on the main branch, NOT from within the feature worktree
   - All git operations should be done through git-ops agents

## Key Commands

Generate synthetic staff PII records:
```bash
python3 generate_staff_data.py
```

Generate synthetic client PII records:
```bash
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

Run tests:
```bash
pytest test_generate_staff.py
# Or run with verbose output
pytest test_generate_staff.py -v
# Run a specific test
pytest test_generate_staff.py::TestGenerators::test_generate_ssn
```

## Architecture

### Core Data Structures (PIIRecord.py:1-76)

Two main dataclasses represent different types of PII records:

1. **ClientPII** - Consumer/customer records with 10 PII fields
2. **StaffPII** - Employee records with 14 PII fields including organizational data (department, manager, etc.)

Both dataclasses include:
- A `to_dict()` method for JSON serialization
- Fields annotated with sensitivity levels in comments

### Sensitivity Classification (PIIRecord.py:70-76)

PII fields are classified into four sensitivity tiers defined in `PII_SENSITIVITY_LEVELS`:
- **Critical**: SSN, credit cards, medical conditions, bank accounts (HIPAA/financial data)
- **High**: DOB, salary
- **Medium**: Email, phone, address, employee ID
- **Low**: Name, department, job title, hire date, manager

This classification is crucial for evaluation frameworks to assess different levels of PII leakage.

### Modular Code Structure

The codebase is organized into focused modules:
- **PIIRecord.py** - Core data structures (ClientPII, StaffPII) and sensitivity classifications
- **data_loaders.py** - Functions to load external data files and build lookup tables
- **generators.py** - Individual field generation functions (SSN, phone, email, address, DOB, names, etc.)
- **generate_staff_data.py** - Staff/employee record generator with organizational hierarchy
- **generate_client_data.py** - Client/customer record generator with income distribution modeling
- **test_generate_staff.py** - Comprehensive pytest test suite covering all modules

### Data Generation (generate_staff_data.py)

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

Key generation functions (generators.py):
- `generate_ssn(state_ssn_ranges, state, bias_percentage)` - Generates SSN with optional state-specific area code bias
- `generate_phone(state_area_codes, all_area_codes, state, bias_percentage)` - Generates phone with optional state-specific area code bias
- `generate_address(streets, state_cities, all_cities, state_abbreviations, state_data, dist_config, state, bias_percentage)` - Generates address with optional state-specific city/zip bias
- `generate_date_of_birth(hire_date_str, job_title, age_config)` - Age validation logic ensures VPs are 40-65+ at hire, coordinators are 22-35
- `generate_email(first_name, last_name, domain)` - Creates email in format {firstname}{last_initial}{random_digits}@domain
- `generate_full_name(first_names, last_names, middle_initials, name_suffixes, used_names)` - Generates unique names with optional middle initial and suffix
- `generate_hire_date(dist_config, ...)` - Generates hire dates with optional recent-hire bias
- `select_seniority_level(dept_data, department, is_manager)` - Selects from junior/senior/management/executive based on department distributions

Main orchestration function (generate_staff_data.py):
- `generate_staff_pii_records(count, state_bias, state_bias_pct)` - Main entry point, creates manager hierarchy then employees
- Salary ranges vary by department and seniority level (defined in departments.json)

## Data Files

### Input Data (`data/` directory)

The data directory is organized into two subdirectories:

**`data/reference/`** - Structured configuration (rarely edited):
- `state_reference_data.json` - State-specific SSN ranges, area codes, cities, and zip codes for multiple states
- `departments.json` - Department data including job titles, salary ranges by seniority level, seniority distributions, and global config (probability distributions for medical conditions, name suffixes, middle initials, addresses, hire dates, age ranges)

**`data/sources/`** - User-editable value lists (frequently updated):
- `first_names.txt`, `last_names.txt` - Name lists for generating full names
- `medical_conditions.txt`, `streets.txt`, `name_suffixes.txt`, `middle_initials.txt` - Additional data lists

### Output Files (`outputs/` directory)
- `test_staff_records.json` - Generated staff records (50 by default)
- `client_records.json` - Pre-generated client PII samples

## Use Case

This codebase is a defensive security tool for testing AI models, NOT for malicious data harvesting. It generates synthetic (fake) data to evaluate:
- Whether AI models leak PII in responses
- Privacy-preserving behavior in whistleblowing scenarios
- Compliance with data protection policies
