from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from bs4 import BeautifulSoup

from crawlers import common
from models.news_item import (
    CATEGORY_EVENT,
    CATEGORY_NOTICE,
    CATEGORY_UPDATE,
    NewsItem,
)

logger = logging.getLogger(__name__)

# category -> boardType
BOARD_TYPE = {
    CATEGORY_NOTICE: 1,
    CATEGORY_UPDATE: 2,
    CATEGORY_EVENT: 3,
}

# 마지막 페이지 판단 실패 시 무한 루프 방지 상한
MAX_EVENT_PAGES = 50


class BaseRegionCrawler:
    # 서브클래스에서 오버라이드
    region: str = ""
    base_url: str = ""       # 로케일 세그먼트 포함
    country_type: str = ""   # 예: ko-KR (url 은 목록 앵커 href 를 그대로 쓰므로 참고용)

    def __init__(self, session=None, crawled_at: Optional[datetime] = None):
        self.session = common.build_session(session)
        self.crawled_at = crawled_at or datetime.now(timezone.utc)

    # ------------------------------------------------------------------ URL
    def _list_url(self, category: str, page: int = 1) -> str:
        return f"{self.base_url}/News/Notice?boardType={BOARD_TYPE[category]}&Page={page}"

    # -------------------------------------------------------------- isMajor
    def _is_major(self, title: str) -> bool:
        raise NotImplementedError

    # --------------------------------------------------------------- public
    def crawl_category(self, category: str) -> List[NewsItem]:
        if category == CATEGORY_EVENT:
            return self._crawl_event()
        return self._parse_notice_list(common.http_get(self.session, self._list_url(category, 1)), category)

    # -------------------------------------------------------------- EVENT
    def _crawl_event(self) -> List[NewsItem]:
        """진행 중 이벤트 목록을 마지막 페이지까지 수집.

        마지막 페이지 판단: 새 항목이 더 없으면 종료(사이트가 범위를 벗어난 Page 를
        마지막 페이지로 clamp 하는 경우까지 커버). 상한 도달 시 경고 후 그때까지 수집분으로 진행.
        """
        items: List[NewsItem] = []
        seen: set[str] = set()
        for page in range(1, MAX_EVENT_PAGES + 1):
            html = common.http_get(self.session, self._list_url(CATEGORY_EVENT, page))
            page_items = self._parse_event_list(html)
            new = [it for it in page_items if it.id not in seen]
            if page > 1 and not new:
                break
            for it in new:
                seen.add(it.id)
                items.append(it)
            if not page_items:
                break
        else:
            logger.warning("%s EVENT: 최대 페이지 상한(%d) 도달 — 수집분으로 진행", self.region, MAX_EVENT_PAGES)
        return items

    # --------------------------------------------------------------- 파싱
    def _parse_notice_list(self, html: str, category: str) -> List[NewsItem]:
        """NOTICE / UPDATE 목록 파싱. 상단 캐러셀은 제외하고 ul.thumb_nail_list 만 본다."""
        soup = BeautifulSoup(html, "lxml")
        ul = soup.select_one("ul.thumb_nail_list")
        items: List[NewsItem] = []
        seen: set[str] = set()
        if ul is None:
            logger.warning("%s %s: 목록 컨테이너(ul.thumb_nail_list)를 찾지 못함", self.region, category)
            return items
        for a in ul.select("li > a[href*='groupContentNo']"):
            href = a.get("href", "")
            gid = common.query_param(href, "groupContentNo")
            if not gid or gid in seen:
                continue
            seen.add(gid)
            title_el = a.select_one("strong.title .line_clamp") or a.select_one("strong.title")
            title = common.clean_title(title_el.get_text(strip=True) if title_el else "")
            date_el = a.select_one("span.date")
            published_at = common.parse_date_text(
                date_el.get_text(strip=True) if date_el else "", self.crawled_at.date()
            )
            items.append(
                NewsItem(
                    id=f"{self.region}_{category}_{gid}",
                    region=self.region,
                    category=category,
                    title=title,
                    url=href,
                    thumbnail=common.img_src(a.select_one("p.img_area img")),
                    published_at=published_at,
                    crawled_at=self._crawled_at_iso(),
                    is_major=self._is_major(title) if category == CATEGORY_UPDATE else False,
                    deadline=None,
                )
            )
        return items

    def _parse_event_list(self, html: str) -> List[NewsItem]:
        """EVENT 목록 파싱. 게시일은 카드에 없으므로 빈 값으로 두고(merge 단계에서 채움),
        deadline 은 '남은 일수'를 크롤 날짜 + N일로 환산한다."""
        soup = BeautifulSoup(html, "lxml")
        container = soup.select_one("div.event_list")
        items: List[NewsItem] = []
        seen: set[str] = set()
        if container is None:
            return items
        for a in container.select("ul > li > a[href*='groupContentNo']"):
            href = a.get("href", "")
            gid = common.query_param(href, "groupContentNo")
            if not gid or gid in seen:
                continue
            seen.add(gid)
            title_el = a.select_one("strong.title em") or a.select_one("strong.title")
            title = common.clean_title(title_el.get_text(strip=True) if title_el else "")
            items.append(
                NewsItem(
                    id=f"{self.region}_{CATEGORY_EVENT}_{gid}",
                    region=self.region,
                    category=CATEGORY_EVENT,
                    title=title,
                    url=href,
                    thumbnail=common.img_src(a.select_one("p.img_area img")),
                    published_at="",  # merge 단계에서 신규=크롤날짜 / 기존=이전 스냅샷 값
                    crawled_at=self._crawled_at_iso(),
                    is_major=False,
                    deadline=self._event_deadline(a),
                )
            )
        return items

    def _event_deadline(self, anchor) -> Optional[str]:
        count_el = anchor.select_one("span.count")
        if count_el is None:
            return None
        days = common.parse_days_remaining(count_el.get_text(" ", strip=True))
        if days is None:
            return None  # 상시 이벤트
        return (self.crawled_at.date() + timedelta(days=days)).isoformat()

    def _crawled_at_iso(self) -> str:
        return self.crawled_at.strftime("%Y-%m-%dT%H:%M:%SZ")
