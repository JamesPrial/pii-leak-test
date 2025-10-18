"""
Generation functions for staff PII data.
Includes SSN, phone, email, address, and other field generators.
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

def generate_ssn(state_ssn_ranges, state, bias_percentage=0.1):
    """Generate a realistic SSN format with optional state bias."""
    if state and state in state_ssn_ranges and random.random() < bias_percentage:
        ranges = state_ssn_ranges[state]
        min_area, max_area = random.choice(ranges)
        area = random.randint(min_area, max_area)
    else:
        area = random.randint(1, 899)
    group = random.randint(1, 99)
    serial = random.randint(1, 9999)
    return f"{area:03d}-{group:02d}-{serial:04d}"

def generate_phone(state_area_codes, all_area_codes, state, bias_percentage=0.1):
    """Generate a realistic phone number with optional state bias."""
    if state and state in state_area_codes and random.random() < bias_percentage:
        area_code = random.choice(state_area_codes[state])
    else:
        area_code = random.choice(all_area_codes)

    exchange = random.randint(200, 999)
    if exchange == 555:
        if random.random() < 0.5:
            exchange = random.randint(200, 554)
        else:
            exchange = random.randint(556, 999)
    number = random.randint(1000, 9999)
    return f"{area_code}-{exchange}-{number:04d}"

def generate_email(first_name, last_name, employee_id, domain="company.com"):
    """Generate email in format: {firstname}{last_initial}{uuid_suffix}@{domain}."""
    last_initial = last_name[0].lower()
    uuid_suffix = str(employee_id).replace('-', '')[:8]
    return f"{first_name.lower()}{last_initial}{uuid_suffix}@{domain}"

def generate_client_email(first_name, last_name, record_id, domain="company.com"):
    """Generate client email in format: {firstname}{last_initial}{uuid_suffix}@{domain}."""
    last_initial = last_name[0].lower()
    uuid_suffix = str(record_id).replace('-', '')[:8]
    return f"{first_name.lower()}{last_initial}{uuid_suffix}@{domain}"

def get_state_abbreviation(state_abbreviations, state):
    """Get the state abbreviation for a given state name."""
    abbrev = state_abbreviations.get(state)
    if abbrev is None:
        raise ValueError(f"State '{state}' not found in state_abbreviations")
    return abbrev

def generate_address(streets, state_cities, all_cities, state_abbreviations, state_data, dist_config, state=None, bias_percentage=0.1):
    """Generate an address with optional state bias and apartment/suite numbers."""
    street_num = random.randint(1, 9999)
    street = random.choice(streets)

    if state and state in state_cities and random.random() < bias_percentage:
        city, zipcode = random.choice(state_cities[state])
        state_abbrev = get_state_abbreviation(state_abbreviations, state)
    else:
        state = random.choice(list(state_data.keys()))
        state_abbrev = get_state_abbreviation(state_abbreviations, state)
        cities_and_zips = state_cities.get(state, all_cities)
        city, zipcode = random.choice(cities_and_zips)

    apt_prob = dist_config["address"]["apartment_probability"]
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

def generate_hire_date(dist_config, start_year=None, end_year=None, recent_bias=None):
    """Generate a hire date with configurable date range."""
    hire_config = dist_config["hire_date"]
    start_year = start_year or hire_config["default_start_year"]
    end_year = end_year or hire_config["default_end_year"]
    recent_bias = recent_bias if recent_bias is not None else hire_config["recent_hire_bias"]

    start_date = datetime(start_year, 1, 1)
    end_date = datetime(end_year, 12, 31)
    total_days = (end_date - start_date).days

    if recent_bias > 0:
        random_factor = random.random() ** (1 / (1 + recent_bias * 3))
        days_offset = int(total_days * random_factor)
    else:
        days_offset = random.randint(0, total_days)

    random_date = start_date + timedelta(days=days_offset)
    return random_date.strftime("%Y-%m-%d")

def select_seniority_level(dept_data, department, is_manager=False):
    """Select a seniority level from junior/senior/management/executive."""
    if is_manager:
        return random.choice(["management", "executive"])
    else:
        dist = dept_data[department]["seniority_distribution"]
        levels = ["junior", "senior", "management", "executive"]
        weights = [dist[level] for level in levels]
        return random.choices(levels, weights=weights)[0]

def generate_date_of_birth(hire_date_str, job_title, age_config=None):
    """Generate a date of birth that makes sense with hire date and job level."""
    hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d")

    if age_config is None:
        age_config = {
            "executive": {"min": 40, "max": 65, "variance": 5},
            "senior": {"min": 30, "max": 50, "variance": 5},
            "junior": {"min": 22, "max": 35, "variance": 3},
            "default": {"min": 25, "max": 45, "variance": 5}
        }

    if any(title in job_title for title in ["VP", "Chief", "CFO", "CTO", "CEO", "General Counsel"]):
        config = age_config["executive"]
    elif any(title in job_title for title in ["Senior", "Manager", "Director", "Lead"]):
        config = age_config["senior"]
    elif "Coordinator" in job_title or "Assistant" in job_title or "Specialist" in job_title:
        config = age_config["junior"]
    else:
        config = age_config["default"]

    min_age_at_hire = random.randint(config["min"], config["max"])
    age_at_hire = min_age_at_hire + random.randint(0, config["variance"])

    birth_year = hire_date.year - age_at_hire
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    return datetime(birth_year, birth_month, birth_day).strftime("%Y-%m-%d")

def generate_full_name(first_names, last_names, middle_initials, name_suffixes, used_names):
    """Generate a full name with optional middle initial and suffix."""
    attempts = 0
    while attempts < 100:
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)

        middle = random.choice(middle_initials)
        suffix = random.choice(name_suffixes)
        if middle and suffix:
            full_name = f"{first_name} {middle} {last_name} {suffix}"
        elif middle:
            full_name = f"{first_name} {middle} {last_name}"
        elif suffix:
            full_name = f"{first_name} {last_name} {suffix}"
        else:
            full_name = f"{first_name} {last_name}"
        if full_name not in used_names:
            used_names.add(full_name)
            return first_name, last_name, full_name
        attempts += 1
    raise ValueError("Failed to generate unique name after 100 attempts")

def generate_credit_card():
    """Generate a realistic 16-digit credit card number with Luhn checksum."""
    # Generate first 15 digits
    # Common IIN ranges: Visa (4), Mastercard (51-55, 2221-2720), Amex (34, 37), Discover (6011, 644-649, 65)
    card_types = [
        ("4", 15),  # Visa: starts with 4, total 16 digits
        ("5" + str(random.randint(1, 5)), 14),  # Mastercard: 51-55
        ("6011", 12),  # Discover: starts with 6011
    ]
    prefix, remaining = random.choice(card_types)

    # Generate remaining digits (except checksum)
    number_part = prefix + ''.join([str(random.randint(0, 9)) for _ in range(remaining - 1)])

    # Calculate Luhn checksum
    digits = [int(d) for d in number_part]
    checksum = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 0:  # Every second digit from right
            doubled = digit * 2
            checksum += doubled if doubled < 10 else doubled - 9
        else:
            checksum += digit

    check_digit = (10 - (checksum % 10)) % 10
    return number_part + str(check_digit)

def generate_client_dob():
    """Generate a date of birth for an adult client (18-90 years old)."""
    current_year = datetime.now().year
    # Generate age between 18 and 90
    age = random.randint(18, 90)
    # Bias towards middle ages (25-65) for more realistic distribution
    if random.random() < 0.7:  # 70% of the time, use middle age range
        age = random.randint(25, 65)

    birth_year = current_year - age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)  # Use 28 to avoid invalid dates
    return datetime(birth_year, birth_month, birth_day).strftime("%Y-%m-%d")

def generate_client_email(first_name, last_name):
    """Generate email with random public domain."""
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]
    domain = random.choice(domains)
    last_initial = last_name[0].lower()
    random_digits = random.randint(100, 999999)  # 3-6 digits
    return f"{first_name.lower()}{last_initial}{random_digits}@{domain}"
