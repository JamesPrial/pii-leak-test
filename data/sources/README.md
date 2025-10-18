# Data Sources

This directory contains simple text lists used to generate synthetic PII records for AI safety testing. Each file contains one value per line.

## Files

- **first_names.txt** - Common first names for generating employee/client identities
- **last_names.txt** - Common last names for generating employee/client identities
- **medical_conditions.txt** - Sample medical conditions (HIPAA-sensitive data for testing)
- **streets.txt** - Street names for generating realistic addresses
- **middle_initials.txt** - Letters A-Z for middle initials
- **name_suffixes.txt** - Name suffixes (Jr., Sr., III, etc.)

## How to Add More

Simply add new entries to the relevant .txt file, one per line. The generator will randomly select from these values when creating synthetic records.

## Important Notes

- **Purpose**: These lists are for generating synthetic (fake) data for AI safety evaluation only
- **Not actively maintained**: This is a minimal dataset sufficient for testing purposes. I won't be expanding or updating these lists beyond initial setup
- **Use responsibly**: This tool is intended for defensive security testing, not for any malicious purposes

For more context on how this data is used, see the main README and CLAUDE.md in the repository root.
