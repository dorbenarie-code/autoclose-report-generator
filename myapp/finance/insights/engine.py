from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
import importlib
import pkgutil
import yaml
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import List, Any, Optional, Dict
import pandas as pd


class Severity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class Insight:
    code: str
    message: str
    severity: str
    meta: Optional[dict[str, Any]] = None


class InsightsEngine:
    def __init__(self, rules_path: Optional[Path] = None) -> None:
        self.rules_path = rules_path or Path(__file__).parent / "rules.yml"
        self.rules = self._load_rules()
        self.detectors = self._load_detectors()

    def _load_rules(self) -> Any:
        with open(self.rules_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_detectors(self) -> list[Any]:
        detectors = []
        detectors_dir = Path(__file__).parent / "detectors"
        for _, modname, _ in pkgutil.iter_modules([str(detectors_dir)]):
            mod = importlib.import_module(f"myapp.finance.insights.detectors.{modname}")
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if hasattr(obj, "__bases__") and "AbstractDetector" in [
                    b.__name__ for b in obj.__bases__
                ]:
                    detectors.append(obj)
        return detectors

    def generate(self, df: pd.DataFrame) -> List[Insight]:
        ctx = self._pre_aggregate(df)
        insights = []
        for Detector in self.detectors:
            detector = Detector(df, self.rules, ctx)
            insights.extend(detector.detect())
        # מיון לפי חומרה
        return sorted(insights, key=lambda i: Severity[i.severity].value, reverse=True)

    def _pre_aggregate(self, df: pd.DataFrame) -> Dict[str, Any]:
        # ניתן להרחיב: חישובי סיכומים, ממוצעים, קיבוצים
        return {
            "daily": (
                df.groupby("date")
                .agg({"net_income": "sum", "tax_collected": "sum", "job_id": "count"})
                .reset_index()
                if "date" in df.columns
                else pd.DataFrame()
            )
        }
