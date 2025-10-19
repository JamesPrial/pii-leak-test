# PII Leak Test - Synthetic Data Generator

Generate realistic synthetic PII (Personally Identifiable Information) datasets for testing AI model behavior in whistleblowing and data privacy scenarios. Built for use with [Petri](https://github.com/safety-research/petri), an AI safety evaluation tool based on the Inspect AI framework.

## Quick Start

Generate synthetic staff PII records:

```bash
cd src/generate
python3 generate_staff_data.py
```

This creates `../../synth/test_staff_records.json` with 50 realistic employee records containing various PII fields.

## Data Structures

Two PII record types are supported:
- **StaffPII** (14 fields) - Employee records with organizational hierarchy, banking details, optional medical conditions
- **ClientPII** (10 fields) - Customer records with credit cards and consumer data

PII fields are classified into four sensitivity tiers (Critical/High/Medium/Low) for AI safety evaluation.

**For detailed field definitions, sensitivity classifications, and usage examples**, see [src/types/README.md](src/types/README.md)

## Use Cases

Test AI models for:
- PII leakage in responses
- Privacy-preserving behavior
- Compliance with data protection policies
- Whistleblowing scenario handling

Designed for integration with Petri evaluation framework to assess model safety around sensitive data.

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Comprehensive developer documentation and workflow guidelines
- **[src/types/README.md](src/types/README.md)** - Type definitions and sensitivity classifications
- **[src/generate/README.md](src/generate/README.md)** - Data generation scripts and CLI usage
- **[src/database/README.md](src/database/README.md)** - Database setup and management
- **[data/reference/README.md](data/reference/README.md)** - Reference data file formats
- **[data/sources/README.md](data/sources/README.md)** - Editable source data lists

## Key Files

- `src/types/` - Data structures and sensitivity classifications
- `src/generate/` - Data generation scripts
- `src/database/` - PostgreSQL database setup
- `synth/` - Generated synthetic data output
