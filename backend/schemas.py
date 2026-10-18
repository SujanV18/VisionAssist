from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
import re

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class LoginInput(Input):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

class EnquiryInput(Input):
    name: str = Field(min_length=2, max_length=100)
    contact: str = Field(min_length=7, max_length=254)
    property_type: Literal['Home', 'Shop', 'Office', 'Warehouse', 'Other']
    location: str = Field(min_length=2, max_length=200)
    requirements: str = Field(min_length=10, max_length=4000)
    referral_code: str | None = Field(default=None, max_length=64)
    consent: Literal[True]

    @field_validator('contact')
    @classmethod
    def contact_is_valid(cls, value):
        if re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            return value
        digits = re.sub(r'[\s()+-]', '', value)
        if digits.isdigit() and 10 <= len(digits) <= 15:
            return value
        raise ValueError('Enter a valid email address or phone number (10-15 digits)')

class AssignmentInput(Input):
    assignee_id: str | None
    revision: int = Field(ge=1)
    reason: str = Field(min_length=3, max_length=500)

class QuoteLine(Input):
    product_id: str
    quantity: int = Field(ge=1, le=100, strict=True)
    lens: Literal['2.8 mm', '4 mm']

class QuoteInput(Input):
    revision: int = Field(ge=1)
    items: list[QuoteLine] = Field(min_length=1, max_length=20)
    notes: str = Field(default='', max_length=2000)
