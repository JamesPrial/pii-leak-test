# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a synthetic PII (Personally Identifiable Information) data generator designed for AI safety evaluation and testing. It generates realistic employee and customer records for testing AI model behavior around data privacy, PII leakage, and whistleblowing scenarios. Built for integration with [Petri](https://github.com/safety-research/petri), an AI safety evaluation tool based on the Inspect AI framework.

## CRITICAL Workflow Requirements

**ALWAYS follow this workflow:**

1. **Use subagents proactively** - Leverage specialized agents where appropriate for tasks like file I/O, git operations, and exploration
2. **Git worktree workflow** - Before beginning any file editing/creation:
   - Use the git-ops agent to check out a new git worktree from main
   - After finishing your changes, commit them
   - Merge your branch with main
   - Delete the worktree
   - Delete the branch you created
   - All git operations should be done through the git-ops agent

## Key Commands

Generate synthetic staff PII records:
```bash
python3 generate_staff_data.py
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

### Data Generation (generate_staff_data.py)

The staff data generator creates realistic records with:
- **External data sources**: Loads from JSON files for maintainability
  - `state_reference_data.json`: State-specific data (SSN ranges, cities, zip codes, area codes) for multiple states
  - `departments.json`: Consolidated department data (job titles and salary ranges per department)
  - `distributions_config.json`: Configurable probability distributions (medical conditions, name suffixes, middle initials, apartments, hire dates, age ranges)
  - `first_names.txt`, `last_names.txt`: Name lists
  - `medical_conditions.txt`, `streets.txt`, `name_suffixes.txt`, `middle_initials.txt`: Additional data lists
- **Geographic focus**: Defaults to New Jersey demographics but supports multi-state generation with configurable bias
  - `state_bias` parameter: Specify state name (e.g., "California", "Texas")
  - `state_bias_pct` parameter: Controls probability of using state-specific data (0.1 = 10% bias)
- **Organizational structure**: Hierarchical manager relationships (first 10% of records are managers)
- **Age-appropriate hiring**: DOB calculation based on job level and hire date using configurable age ranges
- **Realistic distributions**: All distributions configurable via `distributions_config.json`
  - Medical conditions: 60% have none (8:1 weight ratio)
  - Name suffixes: ~67% have none (8:1 weight ratio)
  - Middle initials: ~18% have none (4:1 weight ratio)
  - Addresses: 30% include apartment/suite numbers
  - Hire dates: Configurable date range and recency bias
- **Non-sequential IDs**: Randomized employee IDs to avoid patterns

Key generation functions:
- `generate_staff_pii_records(count, state_bias, state_bias_pct)` - Main entry point, creates manager hierarchy then employees
- `generate_ssn(state, bias_percentage)` - Generates SSN with optional state-specific area code bias
- `generate_phone(state, bias_percentage)` - Generates phone with optional state-specific area code bias
- `generate_address(state, bias_percentage)` - Generates address with optional state-specific city/zip bias
- `generate_date_of_birth(hire_date_str, job_title, age_config)` - Age validation logic ensures VPs are 35-45+ at hire, coordinators are 22-30
- Salary ranges vary by department (Customer Support: $40-120K, Engineering: $150-280K)

## Data Files

### Input Data (`data/` directory)
- `state_reference_data.json` - State-specific SSN ranges, area codes, cities, and zip codes
- `departments.json` - Job titles and salary ranges for 11 departments
- `distributions_config.json` - Configurable probability distributions for data generation
- `first_names.txt`, `last_names.txt` - Name lists
- `medical_conditions.txt`, `streets.txt`, `name_suffixes.txt`, `middle_initials.txt` - Additional data lists

### Output Files (`outputs/` directory)
- `test_staff_records.json` - Generated staff records (50 by default)
- `client_records.json` - Pre-generated client PII samples

## Use Case

This codebase is a defensive security tool for testing AI models, NOT for malicious data harvesting. It generates synthetic (fake) data to evaluate:
- Whether AI models leak PII in responses
- Privacy-preserving behavior in whistleblowing scenarios
- Compliance with data protection policies
