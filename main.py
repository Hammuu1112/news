from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import List

from config import get_config
from crawlers.eu_crawler import EuCrawler
from crawlers.jp_crawler import JpCrawler
from crawlers.kr_crawler import KrCrawler
from crawlers.lab_crawler import LabCrawler
from crawlers.na_crawler import NaCrawler
from models.news_item import (
    ACTION_CREATED,
    CATEGORY_EVENT,
    CATEGORY_LAB,
    CATEGORY_NOTICE,
    CATEGORY_UPDATE,
)
from utils import file_manager, git_manager, webhook

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("main")

# main.py(리포 루트) -> data/news
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(REPO_ROOT, "news")

REGION_CRAWLER_CLASSES = [KrCrawler, NaCrawler, EuCrawler, JpCrawler]
REGION_CATEGORIES = [CATEGORY_NOTICE, CATEGORY_UPDATE, CATEGORY_EVENT]


def _path_for(name: str) -> str:
    return os.path.join(DATA_DIR, f"{name}.json")


def _tag(name: str, changes: List) -> str:
    """커밋 메시지용 태그. 예: 'KR_UPDATE created' / 'KR_EVENT extended'."""
    actions = {action for action, _ in changes}
    parts = []
    if ACTION_CREATED in actions:
        parts.append(f"{name} created")
    if any(a != ACTION_CREATED for a in actions):  # UPDATED
        parts.append(f"{name} extended")
    return ", ".join(parts)


def _commit_message(tags: List[str], item_count: int) -> str:
    inner = ", ".join(t for t in tags if t)
    return f"chore: update news [{inner}] ({item_count} items)"


def main() -> None:
    config = get_config()
    crawled_at = datetime.now(timezone.utc)
    crawl_date_iso = crawled_at.date().isoformat()

    all_changes: List = []       # (action, item)
    changed_paths: List[str] = []
    commit_tags: List[str] = []

    def handle(name: str, category: str, new_items):
        """한 파일(리전×카테고리 또는 LAB)의 diff/저장 처리."""
        path = _path_for(name)
        prev_items = file_manager.read_items(path)
        if category == CATEGORY_EVENT:
            file_manager.apply_event_carryover(prev_items, new_items, crawl_date_iso)
        changes = file_manager.diff(prev_items, new_items, category)
        if not changes:
            logger.info("%s: 변경 없음", name)
            return
        file_manager.write_items(path, new_items)
        all_changes.extend(changes)
        changed_paths.append(path)
        commit_tags.append(_tag(name, changes))
        logger.info("%s: 변경 %d건", name, len(changes))

    # ---- 리전 크롤러 ----
    for crawler_cls in REGION_CRAWLER_CLASSES:
        crawler = crawler_cls(crawled_at=crawled_at)
        for category in REGION_CATEGORIES:
            name = f"{crawler.region}_{category}"
            try:
                new_items = crawler.crawl_category(category)
            except Exception as e:  # 명세 §6-4: 해당 항목만 스킵, 나머지 계속.
                logger.error("크롤 실패 %s (%s) — 스킵", name, e)
                continue
            handle(name, category, new_items)

    # ---- LAB 크롤러 ----
    try:
        lab_items = LabCrawler(crawled_at=crawled_at).crawl()
        handle("LAB", CATEGORY_LAB, lab_items)
    except Exception as e:
        logger.error("크롤 실패 LAB (%s) — 스킵", e)

    # ---- 변경 없으면 종료 ----
    if not all_changes:
        logger.info("변경 사항 없음 — Webhook/커밋 없음")
        return

    # ---- Webhook 먼저, 성공 시에만 커밋 ----
    payload = [item.to_webhook_dict(action) for action, item in all_changes]
    if not webhook.send_with_retry(config, payload):
        logger.error("Webhook 실패로 커밋을 생략하고 종료합니다.")
        sys.exit(1)

    message = _commit_message(commit_tags, len(all_changes))
    git_manager.commit_and_push(changed_paths, message)
    logger.info("완료: %d건 알림 및 커밋", len(all_changes))


if __name__ == "__main__":
    main()
