from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
from .base import AbstractDetector
from myapp.finance.insights.engine import Insight, Severity
import pandas as pd


class Detector(AbstractDetector):
    def detect(self) -> list:
        insights = []
        rule = self.rules.get("INC_DROP", {})
        window = rule.get("window", 3)
        pct = rule.get("pct", 0.3)
        daily = self.ctx.get("daily", pd.DataFrame())
        if daily.empty or "net_income" not in daily:
            return []
        rolling = daily["net_income"].rolling(window).mean()
        for i in range(window, len(rolling)):
            prev = rolling.iloc[i - window]
            curr = rolling.iloc[i]
            if prev > 0 and curr < prev * (1 - pct):
                insights.append(
                    Insight(
                        code="INC_DROP",
                        message=f"Net income dropped by >{int(pct*100)}% over {window} days.",
                        severity=Severity.CRITICAL.name,
                        meta={"from": prev, "to": curr},
                    )
                )
        return insights
