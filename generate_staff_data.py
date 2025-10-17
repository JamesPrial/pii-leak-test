#!/usr/bin/env python3
"""
Generate realistic staff PII records for testing purposes.
"""

import json
import random
from datetime import datetime, timedelta
from PIIRecord import StaffPII

# Load consolidated state data from external JSON file
with open("data/values_by_state.json", "r") as f:
    STATE_DATA = json.load(f)

# Load department data from external JSON file
with open("data/departments.json", "r") as f:
    DEPT_DATA = json.load(f)

# Load distributions configuration from external JSON file
with open("data/distributions_config.json", "r") as f:
    DIST_CONFIG = json.load(f)

# Extract state-specific data
STATE_SSN_RANGES = {state: data["ssn_ranges"] for state, data in STATE_DATA.items()}

# Build state-specific lookup tables for area codes and cities
STATE_AREA_CODES = {
    state: [int(code) for code in data["area_codes"]]
    for state, data in STATE_DATA.items()
}

STATE_CITIES = {
    state: [(city["city"], zip_code)
            for city in data["cities"]
            for zip_code in city["zip_codes"]]
    for state, data in STATE_DATA.items()
}

# For backward compatibility and default NJ focus
NJ_DATA = STATE_DATA["New Jersey"]
NJ_CITIES = STATE_CITIES["New Jersey"]
NJ_AREA_CODES = STATE_AREA_CODES["New Jersey"]

# Build list of all area codes from all states (for fallback)
ALL_AREA_CODES = [code for codes in STATE_AREA_CODES.values() for code in codes]

# Build list of all cities from all states (for fallback)
ALL_CITIES = [(city, state_name) for state_name, cities in STATE_CITIES.items() for city in cities]

# Load first names from external file
with open("data/first_names.txt", "r") as f:
    FIRST_NAMES = [line.strip() for line in f if line.strip()]

# Load last names from external file
with open("data/last_names.txt", "r") as f:
    LAST_NAMES = [line.strip() for line in f if line.strip()]

# Load medical conditions from external file
with open("data/medical_conditions.txt", "r") as f:
    base_conditions = [line.strip() for line in f if line.strip()]
# Use distribution config for medical conditions
med_config = DIST_CONFIG["medical_conditions"]
MEDICAL_CONDITIONS = [None] * med_config["none_weight"] + base_conditions * med_config["condition_weight"]

# Load name suffixes from external file
with open("data/name_suffixes.txt", "r") as f:
    base_suffixes = [line.strip() for line in f if line.strip()]
# Use distribution config for suffixes
suffix_config = DIST_CONFIG["name_suffixes"]
NAME_SUFFIXES = [""] * suffix_config["none_weight"] + base_suffixes * suffix_config["suffix_weight"]

# Load middle initials from external file
with open("data/middle_initials.txt", "r") as f:
    base_initials = [line.strip() for line in f if line.strip()]
# Use distribution config for middle initials
initial_config = DIST_CONFIG["middle_initials"]
MIDDLE_INITIALS = [""] * initial_config["none_weight"] + base_initials * initial_config["initial_weight"]

# Load NJ streets from external file (used as default for all states currently)
with open("data/streets.txt", "r") as f:
    STREETS = [line.strip() for line in f if line.strip()]
    NJ_STREETS = STREETS  # Backward compatibility

def generate_ssn(state=None, bias_percentage=0.1):
    """Generate a realistic SSN format with optional state bias.

    Args:
        state: Optional state name (e.g., "California", "New Jersey") to bias area codes
        bias_percentage: Probability of using state-specific area codes (default 0.1 = 10%)

    Returns:
        SSN string in format XXX-XX-XXXX
    """
    # Apply state-specific bias if state is provided
    if state and state in STATE_SSN_RANGES and random.random() < bias_percentage:
        # Randomly select one of the state's area code ranges
        ranges = STATE_SSN_RANGES[state]
        min_area, max_area = random.choice(ranges)
        area = random.randint(min_area, max_area)
    else:
        # Generate from full valid SSN range
        area = random.randint(1, 899)

    group = random.randint(1, 99)
    serial = random.randint(1, 9999)
    return f"{area:03d}-{group:02d}-{serial:04d}"

def generate_phone(state=None, bias_percentage=0.1):
    """Generate a realistic phone number with optional state bias.

    Args:
        state: Optional state name (e.g., "California", "New Jersey") to bias area codes
        bias_percentage: Probability of using state-specific area codes (default 0.1 = 10%)

    Returns:
        Phone number string in format XXX-XXX-XXXX
    """
    # Apply state-specific bias if state is provided
    if state and state in STATE_AREA_CODES and random.random() < bias_percentage:
        area_code = random.choice(STATE_AREA_CODES[state])
    else:
        # Default to NJ for backward compatibility (or use random state)
        area_code = random.choice(NJ_AREA_CODES)

    exchange = random.randint(200, 999)  # Avoid 555
    if exchange == 555:
        exchange = random.randint(200, 554)
    number = random.randint(1000, 9999)
    return f"{area_code}-{exchange}-{number:04d}"

def generate_email(first_name, last_name):
    """Generate email based on name."""
    return f"{first_name.lower()}.{last_name.lower()}@company.com"

def generate_address(state=None, bias_percentage=0.1):
    """Generate an address with optional state bias and apartment/suite numbers.

    Args:
        state: Optional state name (e.g., "California", "New Jersey") to bias location
        bias_percentage: Probability of using state-specific cities (default 0.1 = 10%)

    Returns:
        Address string with street, optional apt/suite, city, state, zip code
    """
    street_num = random.randint(1, 9999)
    street = random.choice(STREETS)

    # Apply state-specific bias if state is provided
    if state and state in STATE_CITIES and random.random() < bias_percentage:
        city, zipcode = random.choice(STATE_CITIES[state])
        # Get state abbreviation (simple approach - could be externalized)
        state_abbrev = "NJ" if state == "New Jersey" else \
                       "CA" if state == "California" else \
                       "TX" if state == "Texas" else \
                       "FL" if state == "Florida" else \
                       "NY" if state == "New York" else "NJ"
    else:
        # Default to NJ for backward compatibility
        city, zipcode = random.choice(NJ_CITIES)
        state_abbrev = "NJ"

    # Use configured apartment probability
    apt_prob = DIST_CONFIG["address"]["apartment_probability"]
    if random.random() < apt_prob:
        apt_types = ["Apt", "Suite", "Unit"]
        apt_type = random.choice(apt_types)
        if apt_type == "Suite":
            apt_num = random.randint(100, 999)
        else:
            apt_num = random.choice([f"{random.randint(1, 20)}{random.choice(['A', 'B', 'C', 'D', ''])}",
                                     str(random.randint(1, 250))])
        return f"{street_num} {street}, {apt_type} {apt_num}, {city}, {state_abbrev} {zipcode}"

    return f"{street_num} {street}, {city}, {state_abbrev} {zipcode}"

def generate_bank_account():
    """Generate a 16-digit bank account number."""
    return str(random.randint(1000000000000000, 9999999999999999))

def generate_routing_number():
    """Generate a 9-digit routing number."""
    return str(random.randint(100000000, 999999999))

def generate_hire_date(start_year=None, end_year=None, recent_bias=None):
    """Generate a hire date with configurable date range.

    Args:
        start_year: Start year for hire date range (default from config)
        end_year: End year for hire date range (default from config)
        recent_bias: Weight toward recent hires 0.0-1.0 (0=uniform, 1=heavy bias to recent)

    Returns:
        Hire date string in format YYYY-MM-DD
    """
    hire_config = DIST_CONFIG["hire_date"]
    start_year = start_year or hire_config["default_start_year"]
    end_year = end_year or hire_config["default_end_year"]
    recent_bias = recent_bias if recent_bias is not None else hire_config["recent_hire_bias"]

    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    total_days = (end_date - start_date).days

    if recent_bias > 0:
        # Apply bias toward more recent dates using power distribution
        # Higher recent_bias (closer to 1.0) = more weight on recent dates
        random_factor = random.random() ** (1 / (1 + recent_bias * 3))
        days_offset = int(total_days * random_factor)
    else:
        # Uniform distribution
        days_offset = random.randint(0, total_days)

    random_date = start_date + timedelta(days=days_offset)
    return random_date.strftime("%Y-%m-%d")

def generate_date_of_birth(hire_date_str, job_title, age_config=None):
    """Generate a date of birth that makes sense with hire date and job level.

    Args:
        hire_date_str: Hire date in YYYY-MM-DD format
        job_title: Job title to determine appropriate age range
        age_config: Optional dict to override age ranges (defaults to config)

    Returns:
        Date of birth string in format YYYY-MM-DD
    """
    hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d")

    # Use provided age config or default from DIST_CONFIG
    if age_config is None:
        age_config = DIST_CONFIG["age_ranges"]

    # Determine minimum age at hire based on job level
    if any(title in job_title for title in ["VP", "Chief", "CFO", "CTO", "CEO", "General Counsel"]):
        config = age_config["executive"]
    elif any(title in job_title for title in ["Senior", "Manager", "Director", "Lead"]):
        config = age_config["senior"]
    elif "Coordinator" in job_title or "Assistant" in job_title or "Specialist" in job_title:
        config = age_config["junior"]
    else:
        config = age_config["default"]

    # Calculate age at hire using config ranges
    min_age_at_hire = random.randint(config["min"], config["max"])
    age_at_hire = min_age_at_hire + random.randint(0, config["variance"])

    # Calculate birth year
    birth_year = hire_date.year - age_at_hire
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)  # Safe day for all months

    return datetime(birth_year, birth_month, birth_day).strftime("%Y-%m-%d")

def generate_full_name(first_name, last_name):
    """Generate a full name with optional middle initial and suffix."""
    middle = random.choice(MIDDLE_INITIALS)
    suffix = random.choice(NAME_SUFFIXES)
    
    if middle and suffix:
        return f"{first_name} {middle} {last_name} {suffix}"
    elif middle:
        return f"{first_name} {middle} {last_name}"
    elif suffix:
        return f"{first_name} {last_name} {suffix}"
    else:
        return f"{first_name} {last_name}"

def generate_staff_pii_records(count=50, state_bias=None, state_bias_pct=0.1):
    """Generate realistic staff PII records with configurable distributions.

    Args:
        count: Number of records to generate (default 50)
        state_bias: Optional state name to bias geographic data (default None = "New Jersey")
        state_bias_pct: Percentage bias for state-specific data 0.0-1.0 (default 0.1 = 10%)

    Returns:
        List of StaffPII records
    """
    # Default to New Jersey for backward compatibility
    if state_bias is None:
        state_bias = "New Jersey"

    records = []
    managers = []
    used_names = set()

    # Generate random employee IDs (not sequential)
    employee_ids = random.sample(range(1000, 1000 + count * 2), count)
    
    # First, create management positions
    # Ensure manager_count doesn't exceed total count
    manager_count = min(max(1, count // 10), count)
    for i in range(manager_count):
        # Ensure unique names
        attempts = 0
        while attempts < 100:
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            full_name = generate_full_name(first_name, last_name)
            if full_name not in used_names:
                used_names.add(full_name)
                break
            attempts += 1
        
        department = random.choice(list(DEPT_DATA.keys()))
        job_title = random.choice(DEPT_DATA[department]["job_titles"])
        # Try to find a Manager/VP title, but give up after 50 attempts to avoid infinite loops
        attempts_mgr = 0
        while "Manager" not in job_title and "VP" not in job_title and attempts_mgr < 50:
            job_title = random.choice(DEPT_DATA[department]["job_titles"])
            attempts_mgr += 1

        hire_date = generate_hire_date()
        date_of_birth = generate_date_of_birth(hire_date, job_title)
        
        salary_range = DEPT_DATA[department]["salary_range"]
        # Managers get higher end of salary range
        salary = random.randint(int(salary_range[0] * 1.2), salary_range[1])

        medical_condition = random.choice(MEDICAL_CONDITIONS)
        
        record = StaffPII(
            employee_id=f"EMP{employee_ids[i]}",
            name=full_name,
            email=generate_email(first_name, last_name),
            phone=generate_phone(state=state_bias, bias_percentage=state_bias_pct),
            address=generate_address(state=state_bias, bias_percentage=state_bias_pct),
            date_of_birth=date_of_birth,
            ssn=generate_ssn(state=state_bias, bias_percentage=state_bias_pct),
            department=department,
            job_title=job_title,
            hire_date=hire_date,
            manager=None,  # Managers typically don't have managers
            salary=salary,
            bank_account_number=generate_bank_account(),
            routing_number=generate_routing_number(),
            medical_condition=medical_condition
        )
        records.append(record)
        managers.append(full_name)

    # Create remaining employees with manager assignments
    for i in range(manager_count, count):
        # Ensure unique names
        attempts = 0
        while attempts < 100:
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            full_name = generate_full_name(first_name, last_name)
            if full_name not in used_names:
                used_names.add(full_name)
                break
            attempts += 1
            
        department = random.choice(list(DEPT_DATA.keys()))
        job_title = random.choice(DEPT_DATA[department]["job_titles"])

        hire_date = generate_hire_date()
        date_of_birth = generate_date_of_birth(hire_date, job_title)
        
        salary_range = DEPT_DATA[department]["salary_range"]
        salary = random.randint(salary_range[0], salary_range[1])

        medical_condition = random.choice(MEDICAL_CONDITIONS)
        
        record = StaffPII(
            employee_id=f"EMP{employee_ids[i]}",
            name=full_name,
            email=generate_email(first_name, last_name),
            phone=generate_phone(state=state_bias, bias_percentage=state_bias_pct),
            address=generate_address(state=state_bias, bias_percentage=state_bias_pct),
            date_of_birth=date_of_birth,
            ssn=generate_ssn(state=state_bias, bias_percentage=state_bias_pct),
            department=department,
            job_title=job_title,
            hire_date=hire_date,
            manager=random.choice(managers),
            salary=salary,
            bank_account_number=generate_bank_account(),
            routing_number=generate_routing_number(),
            medical_condition=medical_condition
        )
        records.append(record)

    # Shuffle records to avoid sequential ordering
    random.shuffle(records)
    
    return records

def main():
    """Generate staff records and write to JSON file."""
    print("Generating 50 realistic staff PII records...")
    records = generate_staff_pii_records(50)

    # Convert records to dictionaries
    records_dict = [record.to_dict() for record in records]

    # Write to JSON file in outputs directory
    output_file = "outputs/test_staff_records.json"
    with open(output_file, "w") as f:
        json.dump(records_dict, f, indent=2)

    print(f"Successfully generated {len(records)} staff records")
    print(f"Written to {output_file}")
    print(f"\nSample record:")
    print(json.dumps(records_dict[0], indent=2))

if __name__ == "__main__":
    main()
