import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=3, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    is_verified: bool = True
    default_lead_time_days: float | None = Field(default=None, ge=0)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("A valid email address is required")
        return normalized


class SupplierResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str | None = None
    address: str | None = None
    is_verified: bool
    default_lead_time_days: float | None = None

    model_config = ConfigDict(from_attributes=True)
