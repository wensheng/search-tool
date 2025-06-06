"""
Models for the search_tool package.
"""
from typing import Union
from datetime import datetime, timezone

from pydantic import BaseModel, Field, HttpUrl


class BaseResult(BaseModel):
    """Base model for all search result types."""
    title: str
    search_engine: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WebResult(BaseResult):
    url: HttpUrl
    description: str | None = None
    snippet: str | None = None
    display_url: str | None = None
    raw_html_snippet: str | None = None
    position: int | None = None
    sitelinks: list[dict[str, str | HttpUrl]] = Field(default_factory=list)
    source_language: str | None = None
    published_date: datetime | None = None
    is_pdf: bool | None = False
    is_doc: bool | None = False


class ImageResult(BaseResult):
    image_url: HttpUrl
    source_url: HttpUrl
    source_page_title: str | None = None
    thumbnail_url: HttpUrl | None = None
    image_format: str | None = None
    width: int | None = None
    height: int | None = None
    alt_text: str | None = None


class VideoResult(BaseResult):
    url: HttpUrl
    description: str | None = None
    uploader: str | None = None
    platform: str | None = None
    duration: str | None = None
    view_count: int | None = None
    upload_date: datetime | None = None
    thumbnail_url: HttpUrl | None = None
    channel_url: HttpUrl | None = None
    embed_url: HttpUrl | None = None


class NewsResult(BaseResult):
    url: HttpUrl
    snippet: str | None = None
    source_name: str | None = None
    published_date: datetime | None = None
    thumbnail_url: HttpUrl | None = None
    author: list[str] = Field(default_factory=list)


class SearchResults(BaseModel):
    query: str
    search_engine: str
    web_results: list[WebResult] = Field(default_factory=list)
    image_results: list[ImageResult] = Field(default_factory=list)
    video_results: list[VideoResult] = Field(default_factory=list)
    news_results: list[NewsResult] = Field(default_factory=list)
    related_searches: list[str] = Field(default_factory=list)
    corrected_query: str | None = None
    total_estimated_results: int | None = None
    page_load_time_ms: float | None = None