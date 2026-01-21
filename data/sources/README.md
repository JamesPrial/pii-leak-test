# Data Sources

This directory contains simple text lists used to generate synthetic PII records for AI safety testing. Each file contains one value per line.

## Files

| File | Purpose | Entry Count | Used By |
|------|---------|-------------|---------|
| **first_names.txt** | Common first names | ~53 | `generate_staff_data.py`, `generate_client_data.py` |
| **last_names.txt** | Common last names | ~47 | `generate_staff_data.py`, `generate_client_data.py` |
| **medical_conditions.txt** | Medical conditions (HIPAA-sensitive) | ~22 | `generate_staff_data.py` |
| **streets.txt** | Street names for addresses | ~24 | `generate_staff_data.py`, `generate_client_data.py` |
| **middle_initials.txt** | Letters for middle initials | ~18 | `generate_staff_data.py`, `generate_client_data.py` |
| **name_suffixes.txt** | Name suffixes (Jr., Sr., etc.) | ~4 | `generate_staff_data.py`, `generate_client_data.py` |

## File Format

All files use a simple plain text format:
- **Encoding**: UTF-8
- **Line endings**: Unix (LF) or Windows (CRLF) both work
- **One entry per line** - no delimiters needed
- **Empty lines** are ignored during loading
- **No comments** - every non-empty line is treated as data

### Example: first_names.txt
```
Michael
Jennifer
David
Sarah
Christopher
```

### Example: name_suffixes.txt
```
Jr.
Sr.
II
III
```

## How Values Are Used

The generation system loads these files via `data_loaders.py` and selects values randomly:

```python
# From src/generate/data_loaders.py
def load_names_and_conditions(sources_path: str) -> tuple:
    """Load name lists and medical conditions from source files."""
    first_names = _load_list_file(f"{sources_path}/first_names.txt")
    last_names = _load_list_file(f"{sources_path}/last_names.txt")
    medical_conditions = _load_list_file(f"{sources_path}/medical_conditions.txt")
    # ...
```

### Probability Distributions

Some values have **weighted selection** controlled by `data/reference/departments.json`:

| Field | Probability Setting | Default Behavior |
|-------|---------------------|------------------|
| `medical_condition` | `global_config.medical_conditions.default_bias: 0.6` | 60% have no condition |
| `name_suffix` | `global_config.name_suffixes` (8:1 ratio) | ~89% have no suffix |
| `middle_initial` | `global_config.middle_initials` (4:1 ratio) | ~80% have middle initial |

To modify these probabilities, edit `data/reference/departments.json` rather than these source files.

## How to Add More Entries

Simply add new entries to the relevant `.txt` file, one per line:

```bash
# Add a new first name
echo "Olivia" >> first_names.txt

# Add a new medical condition
echo "Chronic Fatigue Syndrome" >> medical_conditions.txt
```

### Validation

After modifying files, verify the generator still works:

```bash
cd src/generate
python3 generate_staff_data.py --count 5
```

Check the output in `synth/test_staff_records.json` to confirm your new values appear.

## Quality Guidelines

### first_names.txt / last_names.txt
- Include a mix of common names across different backgrounds
- Avoid names with unusual characters that might cause encoding issues
- Keep names realistic and representative

### medical_conditions.txt
- Use standard medical terminology
- Include conditions that are relevant to HIPAA-sensitive testing
- Avoid overly rare conditions unless specifically needed

### streets.txt
- Use realistic street name patterns (e.g., "Main Street", "Oak Avenue")
- Include variety: Streets, Avenues, Boulevards, Drives, Courts, etc.
- Avoid specific real addresses

### middle_initials.txt
- Single uppercase letters (A-Z)
- No punctuation needed (periods are added by the generator)

### name_suffixes.txt
- Include punctuation as appropriate (Jr., Sr., III)
- Keep the list small - these are relatively rare

## Important Notes

- **Purpose**: These lists are for generating synthetic (fake) data for AI safety evaluation only
- **Minimal maintenance**: This is a stable dataset sufficient for testing purposes
- **Use responsibly**: This tool is intended for defensive security testing, not for any malicious purposes

## Related Documentation

- **[../reference/README.md](../reference/README.md)** - Structured configuration (states, departments, probabilities)
- **[../../src/generate/README.md](../../src/generate/README.md)** - Data generation scripts and usage
- **[../../CLAUDE.md](../../CLAUDE.md)** - Developer workflow guidelines
