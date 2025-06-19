from myapp.utils.logger_config import get_logger
from decimal import Decimal
from datetime import datetime
import yaml
from pathlib import Path


def load_commission_rules(path: str = "config/commission_rules.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def commission_for(job_type, tech, amount, scheme="percent_50"):
    # Dispatch to myapp/finance/commission.py logic or implement as needed
    from myapp.finance.commission import commission_for as real_commission_for
    return real_commission_for(job_type, tech, amount, scheme)
