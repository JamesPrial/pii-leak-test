from dataclasses import dataclass
from typing import Optional

@dataclass
class ClientPII:
    """Structured PII record with sensitivity levels"""
    record_id: str
    name: str   # Low sensitivity
    email: str  # Medium sensitivity
    phone: str  # Medium sensitivity
    address: str  # Medium sensitivity
    date_of_birth: str  # High sensitivity
    salary: int  # High sensitivity
    medical_condition: str  # Critical sensitivity (HIPAA)
    ssn: str  # Critical sensitivity
    credit_card: str  # Critical sensitivity
    
    def to_dict(self):
        return {
            "record_id": self.record_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "date_of_birth": self.date_of_birth,
            "salary": self.salary,
            "medical_condition": self.medical_condition,
            "ssn": self.ssn,
            "credit_card": self.credit_card
        }

@dataclass
class StaffPII:
    """Structured staff/employee PII record with sensitivity levels"""
    employee_id: str
    name: str   # Low sensitivity
    email: str  # Medium sensitivity
    phone: str  # Medium sensitivity
    address: str  # Medium sensitivity
    date_of_birth: str  # High sensitivity
    ssn: str  # Critical sensitivity
    department: str  # Low sensitivity
    job_title: str  # Low sensitivity
    hire_date: str  # Low sensitivity
    manager: Optional[str]  # Low sensitivity
    salary: int  # High sensitivity
    bank_account_number: str  # Critical sensitivity
    routing_number: str  # Critical sensitivity
    medical_condition: Optional[str]  # Critical sensitivity (HIPAA)

    def to_dict(self):
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "date_of_birth": self.date_of_birth,
            "ssn": self.ssn,
            "department": self.department,
            "job_title": self.job_title,
            "hire_date": self.hire_date,
            "manager": self.manager,
            "salary": self.salary,
            "bank_account_number": self.bank_account_number,
            "routing_number": self.routing_number,
            "medical_condition": self.medical_condition
        }

# Sensitivity classification
PII_SENSITIVITY_LEVELS = {
    "critical": ["ssn", "credit_card", "medical_condition", "bank_account_number", "routing_number"],
    "high": ["dob", "salary"],
    "medium": ["email", "phone", "address", "employee_id"],
    "low": ["name", "department", "job_title", "hire_date", "manager"]
}