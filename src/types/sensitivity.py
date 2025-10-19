# Sensitivity classification
PII_SENSITIVITY_LEVELS = {
    "critical": ["ssn", "credit_card", "medical_condition", "bank_account_number", "routing_number"],
    "high": ["dob", "salary"],
    "medium": ["email", "phone", "address", "employee_id"],
    "low": ["name", "department", "job_title", "hire_date", "manager"]
}
