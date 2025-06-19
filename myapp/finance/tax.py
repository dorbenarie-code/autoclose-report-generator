from decimal import Decimal
from datetime import datetime

_TAX_TABLE = {('IL', 2023): Decimal('0.17'),
              ('IL', 2025): Decimal('0.18')}

def resolve_tax_rate(country: str, date_or_year) -> Decimal:
    if isinstance(date_or_year, datetime):
        year = date_or_year.year
    else:
        year = int(date_or_year)
    return _TAX_TABLE.get((country, year), Decimal('0'))

tax_rate = resolve_tax_rate 