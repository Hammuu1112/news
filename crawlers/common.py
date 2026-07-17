from __future__ import annotations

import logging
import random
import re
import time
from datetime import date
from typing import Optional
from urllib.parse import parse_qs, urlparse

import requests

logger = logging.getLogger(__name__)

# User-Agent 설정 필수, 요청 간 1~2초 딜레이.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 BDO-News-Crawler/1.0"
)
REQUEST_DELAY_RANGE = (1.0, 2.0)  # seconds
REQUEST_TIMEOUT = 15  # seconds

# 썸네일이 없을 때 사이트가 넣는 기본 이미지 파일명 표식.
DEFAULT_THUMB_MARKER = "news_thumb_default"

# KR/JP/LAB 형식: '2026.07.02', '2026.06.26 (UTC+3)'
_DATE_DOT_RE = re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})")
# NA/EU 형식: 'Jul 2, 2026 (UTC)'
_DATE_EN_RE = re.compile(r"([A-Za-z]{3,9})\.?\s+(\d{1,2}),\s*(\d{4})")
_EN_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_INT_RE = re.compile(r"\d+")

# 제목 말미에 사이트가 붙이는 '최종 수정일' 표기(리전별 라벨)를 제거하기 위한 패턴.
#   KR/LAB : '(최종 수정 : 2026-07-03 15:32)'
#   JP     : '(最終更新：...)', '(追記：...)', '(修正：...)'  (전각 콜론 ：)
#   NA/EU  : '(Last Updated: ... UTC)', '(Updated: ... UTC)'
# 라벨이 있는 괄호 세그먼트만 제거하므로 '(금)', '(2026/07/01)' 같은 일반 괄호는 보존한다.
_LAST_MODIFIED_RE = re.compile(
    r"\s*[（(]\s*"
    r"(?:최종\s*수정|最終更新|追記|修正|Last\s+Updated|Updated)"
    r"\s*[:：].*?[)）]\s*$",
    re.IGNORECASE,
)


def clean_title(title: str) -> str:
    """제목에서 말미의 '최종 수정일' 표기를 떼고 앞뒤 공백을 정리한다."""
    return _LAST_MODIFIED_RE.sub("", title or "").strip()


def build_session(session: Optional[requests.Session] = None) -> requests.Session:
    session = session or requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def http_get(session: requests.Session, url: str, delay: bool = True) -> str:
    """정중한 딜레이 후 GET. 실패 시 예외를 그대로 올린다(호출부에서 스킵 처리)."""
    if delay:
        time.sleep(random.uniform(*REQUEST_DELAY_RANGE))
    resp = session.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def query_param(url: str, key: str) -> Optional[str]:
    """URL 쿼리스트링에서 key 값을 뽑는다(예: groupContentNo, _boardNo)."""
    try:
        values = parse_qs(urlparse(url).query).get(key)
        return values[0] if values else None
    except Exception:  # pragma: no cover - 방어적
        return None


def img_src(img_tag) -> str:
    """<img> 태그의 실제 썸네일 URL. 없거나 기본 이미지면 빈 문자열."""
    if img_tag is None:
        return ""
    src = (img_tag.get("src") or "").strip()
    if not src or DEFAULT_THUMB_MARKER in src:
        return ""
    return src


def parse_date_text(text: str, fallback: date) -> str:
    """리전별 게시일 표기를 ISO 날짜(YYYY-MM-DD)로 변환.

    - KR/JP/LAB: '2026.07.02', '2026.06.26 (UTC+3)'
    - NA/EU: 'Jul 2, 2026 (UTC)'
    파싱 실패 시 크롤 날짜(fallback)로 대체한다(publishedAt 은 필수 필드).
    """
    text = text or ""
    m = _DATE_DOT_RE.search(text)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = _DATE_EN_RE.search(text)
    if m:
        month = _EN_MONTHS.get(m.group(1)[:3].lower())
        if month:
            return f"{int(m.group(3)):04d}-{month:02d}-{int(m.group(2)):02d}"
    logger.warning("날짜 파싱 실패 %r -> 크롤 날짜로 대체", text)
    return fallback.isoformat()


def parse_days_remaining(text: str) -> Optional[int]:
    """이벤트 카드의 '7 일 남음' / '24 Days Left' / '21 日で終了' 에서 숫자만 추출.

    숫자가 없으면(상시 이벤트 등) None.
    """
    m = _INT_RE.search(text or "")
    return int(m.group()) if m else None
