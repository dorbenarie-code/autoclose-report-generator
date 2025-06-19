from myapp.utils.logger_config import get_logger

log = get_logger(__name__)
from collections import OrderedDict


class InsightCache:
    def __init__(self, max_size: int = 20):
        self.cache: OrderedDict[str, dict] = OrderedDict()
        self.max_size: int = max_size

    def add(self, insight: dict) -> None:
        self.cache[insight["id"]] = insight
        self.cache.move_to_end(insight["id"])
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def get(self, insight_id: str) -> dict | None:
        return self.cache.get(insight_id)

    def add_many(self, insights: list[dict]) -> None:
        for ins in insights:
            self.add(ins)


INSIGHT_CACHE = InsightCache(max_size=20)
