from pydantic import BaseModel, validator
from typing import Optional
from decimal import Decimal
from datetime import date
from myapp.utils.decimal_utils import safe_decimal
from myapp.utils.parsing_utils import parse_date_flex

class InputRow(BaseModel):
    date: Optional[date]
    total: Decimal
    parts: Decimal
    tech_name: Optional[str]

    @validator("date", pre=True)
    def parse_date(cls, v):
        return parse_date_flex(v)

    @validator("total", "parts", pre=True)
    def to_decimal(cls, v):
        return safe_decimal(v)

    @property
    def tech_profit(self) -> Decimal:
        return (self.total - self.parts) * Decimal("0.5")
