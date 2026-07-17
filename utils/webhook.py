from __future__ import annotations

import logging
from typing import List

import requests

from config import Config

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT = 10  # seconds


def send_notify(config: Config, items: List[dict]) -> requests.Response:
    response = requests.post(
        config.news_notify_url,  # backend_url + news_notify_path 조합
        json={"items": items},
        headers={"Authorization": f"Bearer {config.webhook_secret}"},
        timeout=WEBHOOK_TIMEOUT,
    )
    response.raise_for_status()
    return response


def send_with_retry(config: Config, items: List[dict]) -> bool:
    for attempt in (1, 2):
        try:
            response = send_notify(config, items)
            logger.info(
                "Webhook 성공(시도 %d, %d건): %s", attempt, len(items), response.text[:200]
            )
            return True
        except Exception as e:
            logger.error("Webhook 실패(시도 %d): %s", attempt, e)
    logger.error("Webhook 최종 실패(%d건) — 커밋하지 않아 다음 실행에서 재감지/재전송됨", len(items))
    return False
