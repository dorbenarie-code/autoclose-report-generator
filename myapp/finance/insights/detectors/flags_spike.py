from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
from .base import AbstractDetector
from myapp.finance.insights.engine import Insight, Severity
import pandas as pd


class Detector(AbstractDetector):
    def detect(self) -> list:
        insights = []
        rule = self.rules.get("FLAGS_SPIKE", {})
        threshold = rule.get("threshold", 5)
        if "flags" in self.df.columns and "date" in self.df.columns:
            daily_flags = self.df.groupby("date")["flags"].apply(
                lambda x: x.notna().sum()
            )
            spikes = daily_flags[daily_flags > threshold]
            for date, count in spikes.items():
                insights.append(
                    Insight(
                        code="FLAGS_SPIKE",
                        message=f"{count} red flags on {date}",
                        severity=Severity.WARNING.name,
                        meta={"date": str(date), "count": int(count)},
                    )
                )
        return insights
