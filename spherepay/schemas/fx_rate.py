from pydantic import BaseModel, field_validator
from datetime import datetime
from decimal import Decimal, InvalidOperation
from .. import config

SUPPORTED_CURRENCIES = list(config.INITIAL_BALANCES.keys())

class FxRateUpdate(BaseModel):
    pair: str
    rate: str
    timestamp: datetime

    @field_validator('pair')
    def validate_currency_pair(cls, pair):
        try:
            base, quote = pair.split('/')
            if base not in SUPPORTED_CURRENCIES or quote not in SUPPORTED_CURRENCIES:
                raise ValueError(
                    f"Currency pair {pair} contains unsupported currency. "
                    f"Supported currencies: {', '.join(SUPPORTED_CURRENCIES)}"
                )
            return pair
        except ValueError as e:
            raise ValueError(f"Invalid currency pair format. Error: {str(e)}")

    @field_validator('rate')
    def validate_rate(cls, rate):
        try:
            rate_decimal = Decimal(rate)
            if rate_decimal <= 0:
                raise ValueError("Rate must be positive")
            return rate
        except (ValueError, InvalidOperation) as e:
            raise ValueError(f"Invalid rate format: {str(e)}")

class FxRateResponse(BaseModel):
    pair: str
    rate: str
    timestamp: datetime