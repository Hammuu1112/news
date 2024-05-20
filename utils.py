import json
import logging

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone


def get_description(url: str) -> str:
    response = requests.request(method='get', url=url, headers={'Accept-Language': 'ko-KR,ko;q=0.9'})
    # response.encoding = None
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    description = soup.find('meta', {'name': 'description'}).get('content').strip().replace(u'\xa0', ' ')
    return description


def get_content_id_from_url(url: str) -> str:
    result = "-"
    try:
        result = url.split("?")[-1].split("&")[0].split("=")[1]
    except Exception as e:
        logging.error(f"Cannot parse url: {url}")
    finally:
        return result


def get_date() -> datetime:
    now = (datetime.now(timezone.utc) + timedelta(hours=9)).replace(tzinfo=None)
    now_date = datetime.combine(now, datetime.min.time())
    return now_date


def post_to_webhook(url: str, data: str) -> None:
    headers = {'Content-Type': 'application/json'}
    requests.request('POST', url, data=data, headers=headers)


class WebHookData:
    def __init__(self, title: str, url: str, description: str, thumbnail: str, data_type: str, date: str) -> None:
        self.title = title
        self.url = url
        self.description = description
        self.thumbnail = thumbnail
        self.date = date
        self.data_type = data_type
        self.color_scheme = {
            "event": 4315463,
            "notice": 14238052,
            "update": 6504921,
            "lab": 14251329
        }

    def to_json(self) -> str:
        data = {
            "embeds": [
                {
                    "title": self.title,
                    "description": self.description,
                    "url": self.url,
                    "color": self.color_scheme[self.data_type],
                    "footer": {
                        "text": self.date,
                        "icon_url": "https://www.karanda.kr/assets/assets/icons/bdo.png"
                    },
                    "image": {
                        "url": self.thumbnail
                    }
                }
            ],
            "username": "Karanda",
            "avatar_url": "https://www.karanda.kr/assets/assets/brand/karanda_shape.png",
            "attachments": []
        }
        return json.dumps(data)
