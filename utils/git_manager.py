from __future__ import annotations

import logging
import subprocess
from typing import List

logger = logging.getLogger(__name__)


def _run(args: List[str]) -> subprocess.CompletedProcess:
    logger.info("git %s", " ".join(args))
    return subprocess.run(["git", *args], check=True)


def commit_and_push(paths: List[str], message: str) -> bool:
    """변경 파일을 스테이징 후 커밋·푸시. 스테이징된 변경이 없으면 아무것도 하지 않는다."""
    _run(["add", *paths])
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0
    if not staged:
        logger.info("스테이징된 변경 없음 — 커밋 생략")
        return False
    _run(["commit", "-m", message])
    _run(["push"])
    return True
