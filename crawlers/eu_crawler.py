"""EU 리전 크롤러."""

from __future__ import annotations

from crawlers.na_crawler import NaCrawler


class EuCrawler(NaCrawler):
    region = "EU"
    base_url = "https://www.naeu.playblackdesert.com/en-EU"
    country_type = "en-EU"
