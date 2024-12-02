from pydantic import BaseModel, field_validator
from decimal import Decimal
from datetime import datetime
from typing import Optional
from ..models.transaction import TransactionStatus


class TransactionRequest(BaseModel):
    source_currency: str
    target_currency: str
    source_amount: str  # String to handle decimal precision

    @field_validator('source_currency', 'target_currency')
    def validate_currency(cls, v):
        if v not in {'USD', 'EUR', 'JPY', 'GBP', 'AUD'}:
            raise ValueError(f"Unsupported currency: {v}")
        return v

    @field_validator('source_amount')
    def validate_amount(cls, v):
        try:
            amount = Decimal(v)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            return v
        except Exception as e:
            raise ValueError(f"Invalid amount format: {str(e)}")


class TransactionResponse(BaseModel):
    id: int
    source_currency: str
    target_currency: str
    source_amount: str
    target_amount: str
    fx_rate: str
    margin: str
    status: TransactionStatus
    created_at: datetime
    settled_at: Optional[datetime] = None 