"""NA 리전 크롤러."""

from __future__ import annotations

from crawlers.base_region_crawler import BaseRegionCrawler


class NaCrawler(BaseRegionCrawler):
    region = "NA"
    base_url = "https://www.naeu.playblackdesert.com/en-US"
    country_type = "en-US"

    def _is_major(self, title: str) -> bool:
        # 명세 §4-2: 제목이 "Patch Notes" 로 시작하면 true, 나머지는 false.
        return title.strip().startswith("Patch Notes")
