# PII Leak Test - Synthetic Data Generator

Generate realistic synthetic PII (Personally Identifiable Information) datasets for testing AI model behavior in whistleblowing and data privacy scenarios. Built for use with [Petri](https://github.com/safety-research/petri), an AI safety evaluation tool based on the Inspect AI framework.

## Quick Start

Generate synthetic staff PII records:

```bash
python3 generate_staff_data.py
```

This creates `test_staff_records.json` with 50 realistic employee records containing various PII fields.

## Data Structures

### Staff PII
Employee records with realistic organizational data:
- Employee ID, name, contact info
- Department, job title, manager relationships
- Salary, banking details
- SSN, date of birth
- Medical conditions (optional)

### Client PII
Customer records with consumer data:
- Name, email, phone, address
- SSN, credit card
- Date of birth, salary
- Medical conditions

## Sensitivity Levels

PII fields are classified by sensitivity:
- **Critical**: SSN, credit cards, medical conditions, bank accounts
- **High**: DOB, salary
- **Medium**: Email, phone, address, employee ID
- **Low**: Name, department, job title, hire date

## Use Cases

Test AI models for:
- PII leakage in responses
- Privacy-preserving behavior
- Compliance with data protection policies
- Whistleblowing scenario handling

Designed for integration with Petri evaluation framework to assess model safety around sensitive data.

## Files

- `PIIRecord.py` - Data structures and sensitivity classifications
- `generate_staff_data.py` - Staff record generator (NJ-focused demographics)
- `client_records.json` - Pre-generated client PII samples
- `test_staff_records.json` - Generated staff PII samples
