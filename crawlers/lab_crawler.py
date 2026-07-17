"""연구소(LAB) 크롤러.

- 리전 베이스 클래스와 **완전히 독립**(상속 금지). 공통 유틸 함수(crawlers.common)만 공유.
- ko-KR URL 로만 크롤링, 첫 페이지만 수집. `_boardNo` 를 id 로 사용(LAB_{_boardNo}).
- `_categoryNo=2` 자체가 "업데이트" 카테고리 전용 URL 이다(탭 1/2/4 중 2=업데이트).
- 제목에 "보안 모듈" 이 포함된 항목(보안 모듈 최신 버전 업데이트)은 **제외**한다.
- isMajor 는 항상 true, deadline 은 항상 null.
- 목록 상단 featured 영역에 같은 글이 중복 등장하므로 _boardNo 로 dedupe.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from bs4 import BeautifulSoup

from crawlers import common
from models.news_item import CATEGORY_LAB, REGION_LAB, NewsItem

logger = logging.getLogger(__name__)


class LabCrawler:
    region = REGION_LAB
    base_url = "https://blackdesert.pearlabyss.com/GlobalLab/ko-KR"
    list_path = "/News/Notice?_categoryNo=2"  # _categoryNo=2 = 업데이트 카테고리
    exclude_keyword = "보안 모듈"

    def __init__(self, session=None, crawled_at: Optional[datetime] = None):
        self.session = common.build_session(session)
        self.crawled_at = crawled_at or datetime.now(timezone.utc)

    def crawl(self) -> List[NewsItem]:
        html = common.http_get(self.session, self.base_url + self.list_path)
        soup = BeautifulSoup(html, "lxml")
        ul = soup.select_one("ul.board_list")
        items: List[NewsItem] = []
        seen: set[str] = set()
        if ul is None:
            logger.warning("LAB: 목록 컨테이너(ul.board_list)를 찾지 못함")
            return items
        for li in ul.select("li.board_item"):
            a = li.select_one("a.board_item_inner")
            if a is None:
                continue
            href = a.get("href", "")
            board_no = common.query_param(href, "_boardNo") or a.get("data-boardno")
            if not board_no or board_no in seen:
                continue
            seen.add(board_no)
            title_el = a.select_one("p.title")
            title = common.clean_title(title_el.get_text(strip=True) if title_el else "")
            if self.exclude_keyword in title:
                continue  # 보안 모듈 업데이트 제외
            date_el = a.select_one("span.info_item.date") or a.select_one("span.date")
            published_at = common.parse_date_text(
                date_el.get_text(strip=True) if date_el else "", self.crawled_at.date()
            )
            items.append(
                NewsItem(
                    id=f"LAB_{board_no}",
                    region=REGION_LAB,
                    category=CATEGORY_LAB,
                    title=title,
                    url=href,
                    thumbnail=common.img_src(a.select_one(".img_area img")),
                    published_at=published_at,
                    crawled_at=self.crawled_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    is_major=True,
                    deadline=None,
                )
            )
        return items
