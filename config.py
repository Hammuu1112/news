from __future__ import annotations

import argparse
import os
from dataclasses import dataclass


@dataclass
class Config:
    backend_url: str
    news_notify_path: str
    webhook_secret: str

    @property
    def news_notify_url(self) -> str:
        return f"{self.backend_url.rstrip('/')}/{self.news_notify_path.lstrip('/')}"


def get_config() -> Config:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend-url", default=None, help="로컬 테스트용 오버라이드 (운영에서는 미사용)")
    parser.add_argument("--news-notify-path", default=None, help="로컬 테스트용 오버라이드 (운영에서는 미사용)")
    parser.add_argument("--webhook-secret", default=None, help="로컬 테스트용 오버라이드 (운영에서는 미사용)")
    args, _ = parser.parse_known_args()

    backend_url = args.backend_url or os.environ.get("BACKEND_URL")
    news_notify_path = args.news_notify_path or os.environ.get("NEWS_NOTIFY_PATH")
    webhook_secret = args.webhook_secret or os.environ.get("WEBHOOK_SECRET")

    if not backend_url or not news_notify_path or not webhook_secret:
        raise SystemExit(
            "BACKEND_URL / NEWS_NOTIFY_PATH / WEBHOOK_SECRET 이 설정되지 않았습니다 "
            "(env 또는 CLI 인자 확인)."
        )

    return Config(
        backend_url=backend_url,
        news_notify_path=news_notify_path,
        webhook_secret=webhook_secret,
    )
