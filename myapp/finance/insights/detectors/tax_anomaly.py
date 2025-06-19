from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
from .base import AbstractDetector
from myapp.finance.insights.engine import Insight, Severity
import pandas as pd


class Detector(AbstractDetector):
    def detect(self) -> list:
        insights = []
        rule = self.rules.get("TAX_ANOMALY", {})
        min_rate = rule.get("min_rate", 0.1)
        if "tax_collected" in self.df.columns and "total" in self.df.columns:
            rates = self.df["tax_collected"] / self.df["total"].replace(0, 1)
            anomalies = self.df[rates < min_rate]
            for _, row in anomalies.iterrows():
                insights.append(
                    Insight(
                        code="TAX_ANOMALY",
                        message=f"Tax rate below {min_rate*100:.0f}% for job {row.get('job_id', '')}.",
                        severity=Severity.WARNING.name,
                        meta={"job_id": row.get("job_id", None)},
                    )
                )
        return insights
