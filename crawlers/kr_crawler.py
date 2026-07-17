"""KR 리전 크롤러."""

from __future__ import annotations

from crawlers.base_region_crawler import BaseRegionCrawler


class KrCrawler(BaseRegionCrawler):
    region = "KR"
    base_url = "https://www.kr.playblackdesert.com/ko-KR"
    country_type = "ko-KR"

    # 명세 §4-1: 아래 키워드가 하나라도 포함되면 isMajor=false, 나머지 업데이트는 true.
    _NON_MAJOR_KEYWORDS = ("최신 버전", "보안 모듈", "서버 점검", "임시 점검", "[검은사막+]")

    def _is_major(self, title: str) -> bool:
        return not any(keyword in title for keyword in self._NON_MAJOR_KEYWORDS)
