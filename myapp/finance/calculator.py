from myapp.utils.logger_config import get_logger
import pandas as pd
from myapp.utils.dataframe_utils import enrich as enrich_utils
from myapp.utils.decimal_utils import safe_decimal, apply_safe_decimal

log = get_logger(__name__)


def resolve_commission(row: dict, rules: dict) -> float:
    client = str(row.get("client_id", "")).strip()
    tech = str(row.get("tech", "")).strip()
    service = str(row.get("job_type", "")).strip()

    total = safe_decimal(row.get("total", 0))
    parts = safe_decimal(row.get("parts", 0))
    share = safe_decimal(row.get("tech_share", 0)) / 100 if "tech_share" in row else safe_decimal(0.5)

    rule = rules.get("clients", {}).get(client, {})
    tech_rule = rule.get("techs", {}).get(tech)
    service_rule = rule.get("services", {}).get(service)
    default = rule.get("default") or rules.get("default", {})

    # כלל טכנאי מנצח
    if tech_rule:
        if "flat" in tech_rule:
            return tech_rule["flat"]
        elif "rate" in tech_rule:
            return tech_rule["rate"]

    # כלל שירות משני
    if service_rule:
        return service_rule.get("rate", default.get("rate", 0))

    # ברירת מחדל – רווח × אחוז
    tech_profit = (total - parts) * share
    return round(tech_profit, 2)


def enrich(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
    return enrich_utils(df, *args, **kwargs)
