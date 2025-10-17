# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a synthetic PII (Personally Identifiable Information) data generator designed for AI safety evaluation and testing. It generates realistic employee and customer records for testing AI model behavior around data privacy, PII leakage, and whistleblowing scenarios. Built for integration with [Petri](https://github.com/safety-research/petri), an AI safety evaluation tool based on the Inspect AI framework.

## CRITICAL

ALWAYS PROACTIVELY use subagents where appropriate

Before beginning any file editing/creation/etc, use @agent-git-ops to check out a new working tree from main
After finishing, commit and open a PR, also using @agent-git-ops

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
- **Geographic focus**: New Jersey demographics (NJ area codes, cities, zip codes, street names)
- **Organizational structure**: Hierarchical manager relationships (first 10% of records are managers)
- **Age-appropriate hiring**: DOB calculation based on job level and hire date
- **Realistic distributions**: 60% of records have no medical condition, randomized middle initials/suffixes
- **Non-sequential IDs**: Randomized employee IDs to avoid patterns

Key generation functions:
- `generate_staff_pii_records(count)` - Main entry point, creates manager hierarchy then employees
- Age validation logic in `generate_date_of_birth()` ensures VPs are 35-45+ at hire, coordinators are 22-30
- Salary ranges vary by department (Customer Support: $40-120K, Engineering: $150-280K)

## Output Files

- `test_staff_records.json` - Generated staff records (50 by default)
- `client_records.json` - Pre-generated client PII samples

## Use Case

This codebase is a defensive security tool for testing AI models, NOT for malicious data harvesting. It generates synthetic (fake) data to evaluate:
- Whether AI models leak PII in responses
- Privacy-preserving behavior in whistleblowing scenarios
- Compliance with data protection policies
