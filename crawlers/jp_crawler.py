"""JP 리전 크롤러."""

from __future__ import annotations

from crawlers.base_region_crawler import BaseRegionCrawler


class JpCrawler(BaseRegionCrawler):
    region = "JP"
    base_url = "https://www.jp.playblackdesert.com/ja-JP"
    country_type = "ja-JP"

    def _is_major(self, title: str) -> bool:
        # 제목에 "最新バージョン" 이 포함되면 false, 나머지는 true.
        return "最新バージョン" not in title
