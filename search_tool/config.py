"""
Configuration for the search_tool package.
"""
from enum import StrEnum
from pydantic import BaseModel, Field

MAX_RESULTS = 500


class SearchEngine(StrEnum):
    google = "google"
    duckduckgo = "duckduckgo"
    brave = "brave"


class SafeSearch(StrEnum):
    off = "off"
    moderate = "moderate"
    on = "on"


class TimeRange(StrEnum):
    any = "any"
    past_day = "past_day"
    past_week = "past_week"
    past_month = "past_month"
    past_year = "past_year"


class SearchConfig(BaseModel):
    search_engine: SearchEngine = Field(default=SearchEngine.google)
    num_results: int = Field(default=10, ge=1)
    language: str | None = None
    region: str | None = None
    safe_search: SafeSearch = Field(default=SafeSearch.off)
    time_range: TimeRange = Field(default=TimeRange.any)
    user_agent: str | None = None
    proxy: str | None = None
    headless: bool = Field(default=True)

    def __init__(self, **data):
        super().__init__(**data)
        self.num_results = min(self.num_results, MAX_RESULTS)
