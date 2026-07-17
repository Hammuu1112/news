from __future__ import annotations

import json
import logging
import os
from typing import List, Tuple

from models.news_item import (
    ACTION_CREATED,
    ACTION_UPDATED,
    CATEGORY_EVENT,
    NewsItem,
)

logger = logging.getLogger(__name__)

Change = Tuple[str, NewsItem]  # (action, item)


def read_items(path: str) -> List[NewsItem]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return [NewsItem.from_dict(d) for d in data]
    except Exception as e:  # 손상 파일도 크롤링을 막지 않는다.
        logger.error("파일 읽기 실패 %s: %s", path, e)
        return []


def _sort_key(item: NewsItem):
    # publishedAt 내림차순, 동률 시 id 내림차순(안정적 정렬로 불필요한 diff 노이즈 방지).
    return (item.published_at, item.id)


def write_items(path: str, items: List[NewsItem]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ordered = sorted(items, key=_sort_key, reverse=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([it.to_dict() for it in ordered], f, ensure_ascii=False, indent=2)
        f.write("\n")


def apply_event_carryover(
    prev_items: List[NewsItem], new_items: List[NewsItem], crawl_date_iso: str
) -> None:
    prev = {it.id: it for it in prev_items}
    for it in new_items:
        prev_item = prev.get(it.id)
        it.published_at = prev_item.published_at if prev_item else crawl_date_iso


def diff(prev_items: List[NewsItem], new_items: List[NewsItem], category: str) -> List[Change]:
    prev = {it.id: it for it in prev_items}
    changes: List[Change] = []
    for it in new_items:
        prev_item = prev.get(it.id)
        if prev_item is None:
            changes.append((ACTION_CREATED, it))
        elif category == CATEGORY_EVENT and it.deadline != prev_item.deadline:
            changes.append((ACTION_UPDATED, it))
    return changes
