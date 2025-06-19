from decimal import Decimal

def commission_for(job_type, tech, amount, scheme="percent_50") -> Decimal:
    if scheme == "percent_50":
        return Decimal(amount) * Decimal("0.50")
    elif scheme.startswith("flat_"):
        return Decimal(scheme.split("_")[1])
    elif scheme.startswith("tiered"):
        # very naive tiered example
        if Decimal(amount) <= 500:
            return Decimal(amount) * Decimal("0.30")
        return Decimal(amount) * Decimal("0.20")
    raise ValueError("unknown commission scheme") 