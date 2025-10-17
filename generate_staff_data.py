#!/usr/bin/env python3
"""
Generate realistic staff PII records for testing purposes.
"""

import json
import random
from datetime import datetime, timedelta
from PIIRecord import StaffPII

# Sample data for generating realistic records
FIRST_NAMES = [
    "James", "Sarah", "Michael", "Jennifer", "David", "Emily", "Robert", "Jessica",
    "William", "Amanda", "Richard", "Michelle", "Joseph", "Lisa", "Thomas", "Karen",
    "Charles", "Nancy", "Christopher", "Maria", "Daniel", "Sandra", "Matthew", "Ashley",
    "Mark", "Brenda", "Donald", "Stephanie", "Steven", "Catherine", "Paul", "Deborah",
    "Andrew", "Cheryl", "Joshua", "Carolyn", "Kevin", "Diana", "Brian", "Pamela",
    "Edward", "Kathleen", "Ronald", "Florence", "Anthony", "Teresa", "Frank", "Gloria",
    "Ryan", "Sara", "Gary", "Candice", "Nicholas", "Brittany"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Young",
    "Allen", "King", "Wright", "Scott", "Torres", "Peterson", "Phillips", "Campbell",
    "Parker", "Evans", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales"
]

DEPARTMENTS = [
    "Engineering", "HR", "Sales", "Marketing", "Finance",
    "Operations", "Legal", "IT", "Customer Support", "Product", "Design"
]

JOB_TITLES_BY_DEPT = {
    "Engineering": ["Senior Engineer", "Software Engineer", "DevOps Engineer", "Engineering Manager", "VP Engineering"],
    "HR": ["HR Manager", "HR Specialist", "Recruiter", "VP HR", "HR Coordinator"],
    "Sales": ["Sales Representative", "Account Executive", "Sales Manager", "VP Sales", "Sales Director"],
    "Marketing": ["Marketing Manager", "Content Marketing Specialist", "Marketing Coordinator", "VP Marketing", "Product Marketing Manager"],
    "Finance": ["Accountant", "Financial Analyst", "CFO", "Controller", "Finance Manager"],
    "Operations": ["Operations Manager", "Operations Specialist", "VP Operations", "Supply Chain Manager"],
    "Legal": ["Lawyer", "Legal Counsel", "General Counsel", "Legal Assistant"],
    "IT": ["IT Support Specialist", "IT Manager", "System Administrator", "CTO", "IT Director"],
    "Customer Support": ["Support Specialist", "Support Team Lead", "VP Customer Support", "Support Manager"],
    "Product": ["Product Manager", "Senior Product Manager", "VP Product", "Product Analyst"],
    "Design": ["UX Designer", "UI Designer", "Design Manager", "VP Design", "Senior Designer"]
}

SALARY_RANGES = {
    "Engineering": [150000, 280000],
    "HR": [65000, 160000],
    "Sales": [70000, 200000],
    "Marketing": [65000, 180000],
    "Finance": [75000, 220000],
    "Operations": [60000, 170000],
    "Legal": [120000, 280000],
    "IT": [70000, 250000],
    "Customer Support": [40000, 120000],
    "Product": [90000, 240000],
    "Design": [70000, 200000]
}

MEDICAL_CONDITIONS = [
    None, None, None, None, None, None, None, None,  # Most have no condition (60%)
    "Type 2 Diabetes", "Hypertension", "High Cholesterol", "Asthma",
    "Migraines", "Allergies", "Seasonal Allergies", "Anxiety Disorder",
    "GERD", "Back Pain", "Arthritis", "Sleep Apnea", "Depression",
    "Hypothyroidism", "Eczema", "Chronic Fatigue", "IBS", "Osteoporosis",
    "Celiac Disease", "Psoriasis", "Fibromyalgia", "Anemia"
]

NAME_SUFFIXES = ["", "", "", "", "", "", "", "", "Jr.", "Sr.", "II", "III"]  # Most have no suffix
MIDDLE_INITIALS = ["", "", "", "", "A.", "B.", "C.", "D.", "E.", "F.", "G.", "H.", "J.", "K.", "L.", "M.", "N.", "P.", "R.", "S.", "T.", "W."]

NJ_STREETS = [
    "Main Street", "Park Avenue", "Washington Street", "Broad Street",
    "Maple Avenue", "Oak Street", "Cedar Lane", "Elm Street",
    "Franklin Avenue", "Lincoln Avenue", "Madison Avenue", "Monroe Street",
    "Jefferson Road", "Adams Street", "Wilson Avenue", "Jackson Street",
    "Central Avenue", "Union Avenue", "River Road", "Highland Avenue",
    "Ridge Road", "Summit Avenue", "Spring Street", "Grove Street"
]

NJ_CITIES = [
    ("Newark", "07102"),
    ("Jersey City", "07302"),
    ("Paterson", "07501"),
    ("Elizabeth", "07201"),
    ("Edison", "08817"),
    ("Woodbridge", "07095"),
    ("Lakewood", "08701"),
    ("Trenton", "08608"),
    ("Clifton", "07011"),
    ("Camden", "08101"),
    ("Princeton", "08540"),
    ("Hoboken", "07030")
]

def generate_ssn():
    """Generate a realistic SSN format."""
    # 10% bias for old NJ SSN area codes (135-158)
    if random.random() < 0.1:
        area = random.randint(135, 158)
    else:
        area = random.randint(1, 899)
    group = random.randint(1, 99)
    serial = random.randint(1, 9999)
    return f"{area:03d}-{group:02d}-{serial:04d}"

def generate_phone():
    """Generate a realistic phone number with valid NJ area codes."""
    area_codes = [201, 551, 732, 908, 973, 609, 856, 862]
    area_code = random.choice(area_codes)
    exchange = random.randint(200, 999)  # Avoid 555
    if exchange == 555:
        exchange = random.randint(200, 554)
    number = random.randint(1000, 9999)
    return f"{area_code}-{exchange}-{number:04d}"

def generate_email(first_name, last_name):
    """Generate email based on name."""
    return f"{first_name.lower()}.{last_name.lower()}@company.com"

def generate_address():
    """Generate a New Jersey address with optional apartment/suite numbers."""
    street_num = random.randint(1, 9999)
    street = random.choice(NJ_STREETS)
    city, zipcode = random.choice(NJ_CITIES)
    
    # 30% chance of having an apartment/suite number
    if random.random() < 0.3:
        apt_types = ["Apt", "Suite", "Unit"]
        apt_type = random.choice(apt_types)
        if apt_type == "Suite":
            apt_num = random.randint(100, 999)
        else:
            apt_num = random.choice([f"{random.randint(1, 20)}{random.choice(['A', 'B', 'C', 'D', ''])}", 
                                     str(random.randint(1, 250))])
        return f"{street_num} {street}, {apt_type} {apt_num}, {city}, NJ {zipcode}"
    
    return f"{street_num} {street}, {city}, NJ {zipcode}"

def generate_bank_account():
    """Generate a 16-digit bank account number."""
    return str(random.randint(1000000000000000, 9999999999999999))

def generate_routing_number():
    """Generate a 9-digit routing number."""
    return str(random.randint(100000000, 999999999))

def generate_hire_date():
    """Generate a hire date between 2013 and 2022."""
    start_date = datetime(2013, 1, 1)
    end_date = datetime(2022, 12, 31)
    random_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
    return random_date.strftime("%Y-%m-%d")

def generate_date_of_birth(hire_date_str, job_title):
    """Generate a date of birth that makes sense with hire date and job level."""
    hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d")
    
    # Determine minimum age at hire based on job level
    if any(title in job_title for title in ["VP", "Chief", "CFO", "CTO", "CEO", "General Counsel"]):
        min_age_at_hire = random.randint(35, 45)
    elif any(title in job_title for title in ["Senior", "Manager", "Director", "Lead"]):
        min_age_at_hire = random.randint(28, 38)
    elif "Coordinator" in job_title or "Assistant" in job_title or "Specialist" in job_title:
        min_age_at_hire = random.randint(22, 30)
    else:
        min_age_at_hire = random.randint(24, 35)
    
    # Add some variance
    age_at_hire = min_age_at_hire + random.randint(0, 8)
    
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

def generate_staff_pii_records(count=50):
    """Generate realistic staff PII records."""
    records = []
    managers = []
    used_names = set()
    used_employee_ids = set()

    # Generate random employee IDs (not sequential)
    employee_ids = random.sample(range(1000, 1000 + count * 2), count)
    
    # First, create management positions
    manager_count = max(5, count // 10)
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
        
        department = random.choice(DEPARTMENTS)
        job_title = random.choice(JOB_TITLES_BY_DEPT[department])
        while "Manager" not in job_title and "VP" not in job_title:
            job_title = random.choice(JOB_TITLES_BY_DEPT[department])

        hire_date = generate_hire_date()
        date_of_birth = generate_date_of_birth(hire_date, job_title)
        
        salary_range = SALARY_RANGES[department]
        # Managers get higher end of salary range
        salary = random.randint(int(salary_range[0] * 1.2), salary_range[1])

        medical_condition = random.choice(MEDICAL_CONDITIONS)
        
        record = StaffPII(
            employee_id=f"EMP{employee_ids[i]}",
            name=full_name,
            email=generate_email(first_name, last_name),
            phone=generate_phone(),
            address=generate_address(),
            date_of_birth=date_of_birth,
            ssn=generate_ssn(),
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
            
        department = random.choice(DEPARTMENTS)
        job_title = random.choice(JOB_TITLES_BY_DEPT[department])

        hire_date = generate_hire_date()
        date_of_birth = generate_date_of_birth(hire_date, job_title)
        
        salary_range = SALARY_RANGES[department]
        salary = random.randint(salary_range[0], salary_range[1])

        medical_condition = random.choice(MEDICAL_CONDITIONS)
        
        record = StaffPII(
            employee_id=f"EMP{employee_ids[i]}",
            name=full_name,
            email=generate_email(first_name, last_name),
            phone=generate_phone(),
            address=generate_address(),
            date_of_birth=date_of_birth,
            ssn=generate_ssn(),
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

    # Write to JSON file
    output_file = "test_staff_records.json"
    with open(output_file, "w") as f:
        json.dump(records_dict, f, indent=2)

    print(f"Successfully generated {len(records)} staff records")
    print(f"Written to {output_file}")
    print(f"\nSample record:")
    print(json.dumps(records_dict[0], indent=2))

if __name__ == "__main__":
    main()
