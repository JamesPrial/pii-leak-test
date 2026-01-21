# Reference Data Directory

This directory contains structured configuration files that define geographic data and organizational hierarchies for the synthetic PII generator. These files are **rarely edited** and contain normalized, structured data.

For frequently-updated value lists (names, streets, medical conditions, etc.), see the `data/sources/` directory instead.

---

## Files Overview

### `state_reference_data.json`
Geographic and demographic data for US states, including SSN area number ranges, phone area codes, cities, and zip codes. Used for state-biased data generation.

### `departments.json`
Organizational structure definitions including department hierarchies, job titles, salary ranges, seniority distributions, and global probability settings for various PII fields.

---

## state_reference_data.json

### Structure

```json
{
  "StateName": {
    "state_abbrev": "XX",
    "ssn_ranges": [[start, end], ...],
    "area_codes": ["###", "###", ...],
    "cities": [
      {
        "city": "CityName",
        "zip_codes": ["#####", "#####", ...]
      }
    ]
  }
}
```

### Field Descriptions

#### Top Level
- **StateName** (string): Full state name (e.g., "California", "New Jersey"). Used as the lookup key.

#### State Object Fields
- **state_abbrev** (string): Two-letter state abbreviation (e.g., "CA", "NJ")
- **ssn_ranges** (array): SSN area number ranges historically assigned to this state
  - Format: Array of `[start, end]` pairs (inclusive)
  - Example: `[[001, 003], [135, 158]]` means SSNs starting with 001-003 or 135-158
  - Note: SSN area numbers are historical (pre-2011 randomization); used for realistic generation
- **area_codes** (array): Phone area codes for this state
  - Format: Array of strings (e.g., `["201", "551", "609"]`)
- **cities** (array): Major cities with their zip codes
  - Each city object contains:
    - **city** (string): City name
    - **zip_codes** (array): Array of 5-digit zip code strings for that city

### Usage Notes

- **State bias**: When `--state-bias` is used, SSNs and phone numbers have a higher probability of using that state's ranges/area codes
- **Geographic realism**: Cities and zip codes are paired to maintain geographic accuracy
- **Multi-state support**: The generator can create records across all states in this file

### How to Add a New State

1. Find the state's SSN area number ranges from historical SSA records
2. Look up current area codes from NANPA or telecommunications databases
3. Select 5-10 major cities
4. For each city, gather 5-20 representative zip codes

Example:
```json
"Colorado": {
  "state_abbrev": "CO",
  "ssn_ranges": [[521, 524], [650, 653]],
  "area_codes": ["303", "719", "720", "970"],
  "cities": [
    {
      "city": "Denver",
      "zip_codes": ["80202", "80203", "80204", "80205", "80206"]
    },
    {
      "city": "Colorado Springs",
      "zip_codes": ["80903", "80904", "80905", "80906"]
    }
  ]
}
```

---

## departments.json

### Structure

```json
{
  "global_config": { ... },
  "DepartmentName": {
    "seniority_distribution": { ... },
    "junior": { ... },
    "senior": { ... },
    "management": { ... },
    "executive": { ... }
  }
}
```

### Global Config

The `global_config` section defines probability distributions and settings used across all generated records.

#### medical_conditions
Controls the distribution of medical conditions in generated records.

```json
"medical_conditions": {
  "none_weight": 8,
  "condition_weight": 1,
  "default_bias": 0.6,
  "description": "60% have no medical condition"
}
```

- **none_weight** (int): Relative weight for "no condition" (null value)
- **condition_weight** (int): Relative weight for having a condition from the list
- **Result**: 8:1 ratio means ~89% have no condition (8 out of 9), but `default_bias` overrides to 60%
- **To modify**: Change `default_bias` for percentage, or adjust weights for ratio-based selection

#### name_suffixes
Controls whether names have suffixes (Jr., Sr., III, etc.).

```json
"name_suffixes": {
  "none_weight": 8,
  "suffix_weight": 1,
  "description": "~67% have no suffix"
}
```

- **Result**: 8:1 ratio = 8/(8+1) ≈ 88.9% have no suffix
- **To modify**: Increase `suffix_weight` for more suffixes (e.g., 2 = ~75% no suffix, 3 = ~73% no suffix)

#### middle_initials
Controls whether names include middle initials.

```json
"middle_initials": {
  "none_weight": 4,
  "initial_weight": 1,
  "description": "~18% have no middle initial"
}
```

- **Result**: 4:1 ratio = 4/(4+1) = 80% have middle initials
- **To modify**: Equal weights (1:1) would give 50/50 distribution

#### address
Controls apartment/suite number inclusion in addresses.

```json
"address": {
  "apartment_probability": 0.3,
  "description": "30% of addresses include apartment/suite numbers"
}
```

- **apartment_probability** (float): Probability (0.0-1.0) of including "Apt X" or "Suite X"
- **To modify**: 0.5 = 50% have apartments, 0.1 = 10% have apartments

#### hire_date
Controls the range and distribution of employee hire dates.

```json
"hire_date": {
  "default_start_year": 2013,
  "default_end_year": 2022,
  "recent_hire_bias": 0.0,
  "description": "Default hire date range 2013-2022, 0 = uniform distribution"
}
```

- **default_start_year** (int): Earliest hire year
- **default_end_year** (int): Latest hire year
- **recent_hire_bias** (float 0.0-1.0): 0 = uniform distribution, higher values skew toward recent hires
- **To modify**: For more recent hires, set `recent_hire_bias: 0.7` or adjust year range

#### age_ranges
Defines age ranges by seniority level to ensure realistic ages at hire.

```json
"age_ranges": {
  "executive": {
    "min": 35,
    "max": 45,
    "variance": 8,
    "description": "VP, Chief, CFO, CTO, CEO level positions"
  }
}
```

- **min** (int): Base minimum age at hire for this level
- **max** (int): Base maximum age at hire for this level
- **variance** (int): Additional random variance added to range (±variance years)
- **Effective range**: `[min - variance, max + variance]` (e.g., executive = 27-53 years old at hire)
- **Levels**: executive, senior, junior, default

### Department Definitions

Each department (Engineering, HR, Sales, etc.) has identical structure:

#### seniority_distribution
Defines the relative proportions of seniority levels within the department.

```json
"seniority_distribution": {
  "junior": 2,
  "senior": 5,
  "management": 2,
  "executive": 1,
  "description": "Engineering skews senior-heavy (20% junior, 50% senior...)"
}
```

- **Weights**: Ratio of employees at each level
- **Calculation**: `junior_pct = junior / (junior + senior + management + executive)`
- **Example above**: 2/(2+5+2+1) = 2/10 = 20% junior, 5/10 = 50% senior, etc.

#### Seniority Level Objects (junior, senior, management, executive)

Each seniority level contains:

```json
"junior": {
  "job_titles": ["Junior Engineer", "Junior Software Engineer"],
  "salary_range": [150000, 182000]
}
```

- **job_titles** (array): List of job titles randomly selected for this level
- **salary_range** (array): `[minimum, maximum]` annual salary in USD

### How to Add a New Department

1. Copy an existing department structure
2. Define seniority distribution weights based on department characteristics
3. Create 1-3 job titles per seniority level
4. Set realistic salary ranges (junior < senior < management < executive)

Example:
```json
"Data Science": {
  "seniority_distribution": {
    "junior": 3,
    "senior": 4,
    "management": 2,
    "executive": 1,
    "description": "Data Science moderately senior (30% junior, 40% senior, 20% mgmt, 10% exec)"
  },
  "junior": {
    "job_titles": ["Junior Data Analyst", "Data Analyst"],
    "salary_range": [85000, 110000]
  },
  "senior": {
    "job_titles": ["Data Scientist", "Senior Data Scientist"],
    "salary_range": [110000, 150000]
  },
  "management": {
    "job_titles": ["Lead Data Scientist", "Data Science Manager"],
    "salary_range": [150000, 190000]
  },
  "executive": {
    "job_titles": ["VP Data Science", "Chief Data Officer"],
    "salary_range": [190000, 250000]
  }
}
```

### How to Modify Salary Ranges

All salaries in a department can be scaled proportionally:

1. Identify current range (e.g., junior: 65k-88k, executive: 136k-160k)
2. Calculate scaling factor (e.g., 1.15 for 15% increase)
3. Multiply both min and max by the factor
4. Round to nearest $1,000 or $500 for clean numbers

---

## Best Practices

### When to Edit `reference/` vs `sources/`

**Edit `data/reference/` when:**
- Adding new states or cities
- Adjusting salary structures across departments
- Changing organizational distributions (seniority ratios)
- Tuning global probability settings

**Edit `data/sources/` when:**
- Adding new first/last names
- Adding medical conditions
- Adding street names
- Making frequent content updates

### Validation

After editing these files:

1. **JSON syntax**: Ensure valid JSON (no trailing commas, proper quotes)
2. **Test generation**: Run `python3 generate_staff_data.py --count 10`
3. **Check distributions**: Verify seniority levels and salary ranges are realistic
4. **State bias testing**: Test with `--state-bias "YourNewState"` if adding states

### Version Control

These files are checked into git and rarely change. Document significant changes in commit messages:
- "Add Colorado to state reference data"
- "Adjust Engineering salary ranges for 2024 market"
- "Rebalance Sales seniority distribution"

---

## Related Documentation

- **[../sources/README.md](../sources/README.md)** - Frequently-updated value lists (names, streets, medical conditions)
- **[../../src/generate/README.md](../../src/generate/README.md)** - Data generation scripts and CLI usage
- **[../../CLAUDE.md](../../CLAUDE.md)** - Developer workflow guidelines
