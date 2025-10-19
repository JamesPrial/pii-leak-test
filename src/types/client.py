from dataclasses import dataclass

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
