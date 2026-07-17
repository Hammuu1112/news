from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# region 값
REGION_LAB = "LAB"

# category 값
CATEGORY_NOTICE = "NOTICE"
CATEGORY_UPDATE = "UPDATE"
CATEGORY_EVENT = "EVENT"
CATEGORY_LAB = "LAB"

# Webhook action 값
ACTION_CREATED = "CREATED"
ACTION_UPDATED = "UPDATED"


@dataclass
class NewsItem:
    id: str
    region: str
    category: str
    title: str
    url: str
    thumbnail: str
    published_at: str
    crawled_at: str
    is_major: bool
    deadline: Optional[str]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "region": self.region,
            "category": self.category,
            "title": self.title,
            "url": self.url,
            "thumbnail": self.thumbnail,
            "publishedAt": self.published_at,
            "crawledAt": self.crawled_at,
            "isMajor": self.is_major,
            "deadline": self.deadline,
        }

    def to_webhook_dict(self, action: str) -> dict:
        return {"action": action, **self.to_dict()}

    @classmethod
    def from_dict(cls, data: dict) -> "NewsItem":
        return cls(
            id=data["id"],
            region=data["region"],
            category=data["category"],
            title=data.get("title", ""),
            url=data.get("url", ""),
            thumbnail=data.get("thumbnail", ""),
            published_at=data.get("publishedAt", ""),
            crawled_at=data.get("crawledAt", ""),
            is_major=data.get("isMajor", False),
            deadline=data.get("deadline"),
        )
