from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional
from urllib.parse import quote_plus

import feedparser


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    published: Optional[datetime]


class NewsService:
    """Small cached RSS reader for public Doc-related headlines.

    This is the first Project Arena news source. YouTube transcripts, Reddit,
    X approval workflows and persistent Arena Memory belong in later modules.
    """

    def __init__(self, cache_seconds: int = 900) -> None:
        self.cache_seconds = cache_seconds
        self._cached_at = 0.0
        self._cache: list[NewsItem] = []

    def latest(self, limit: int = 5) -> list[NewsItem]:
        now = time.time()
        if self._cache and now - self._cached_at < self.cache_seconds:
            return self._cache[:limit]

        query = quote_plus('"Dr Disrespect"')
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        parsed = feedparser.parse(url)

        items: list[NewsItem] = []
        for entry in parsed.entries[:20]:
            title = str(entry.get("title", "")).strip()
            link = str(entry.get("link", "")).strip()
            if not title or not link:
                continue

            published = None
            raw_date = entry.get("published")
            if raw_date:
                try:
                    published = parsedate_to_datetime(raw_date)
                except (TypeError, ValueError):
                    published = None

            items.append(NewsItem(title=title, url=link, published=published))

        self._cache = items
        self._cached_at = now
        return items[:limit]
