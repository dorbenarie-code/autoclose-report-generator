from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
from .base import AbstractDetector
from myapp.finance.insights.engine import Insight, Severity
import pandas as pd


class Detector(AbstractDetector):
    def detect(self) -> list:
        insights = []
        rule = self.rules.get("HIGH_COMM", {})
        threshold = rule.get("threshold", 0.9)
        if "tech_cut" in self.df.columns and "total" in self.df.columns:
            high_comm = self.df[
                (self.df["total"] > 0)
                & (self.df["tech_cut"] / self.df["total"] > threshold)
            ]
            for _, row in high_comm.iterrows():
                insights.append(
                    Insight(
                        code="HIGH_COMM",
                        message=f"High commission ({row['tech_cut']}/{row['total']}) for job {row.get('job_id', '')}.",
                        severity=Severity.CRITICAL.name,
                        meta={"job_id": row.get("job_id", None)},
                    )
                )
        return insights
