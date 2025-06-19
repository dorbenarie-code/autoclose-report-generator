from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
from typing import Any


class AbstractDetector:
    def __init__(self, df: Any, rules: Any, ctx: Any) -> None:
        self.df = df
        self.rules = rules
        self.ctx = ctx

    def detect(self) -> Any:
        raise NotImplementedError
