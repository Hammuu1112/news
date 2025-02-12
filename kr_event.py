import json
import os

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

from utils import get_description, get_content_id_from_url, get_date, WebHookData, post_to_webhook

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def kr_event(web_hook_url: str):
    with open(os.path.join(BASE_DIR, 'news', 'kr_event.json'), 'r', encoding='utf-8') as file:
        old_events: dict = json.load(file)

    response = requests.request(method='get', url='https://www.kr.playblackdesert.com/ko-KR/News/Notice?boardType=3')
    response.encoding = None
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    data = soup.select('#wrap > div > div > article > div.tab_container > div > div.event_area > div.event_list')[0]
    table = data.findAll('li')

    today = (datetime.now(timezone.utc) + timedelta(hours=9)).replace(tzinfo=None)
    events = {}
    for event in table:
        title = event.find_next('strong').find_next('em').getText().split(' (최종 수정')[0].strip()
        count = event.find_next('span', {'class': 'count'}).getText().replace("  ", " ").strip()
        if count == "상시":
            deadline = "-"
        else:
            deadline = (today + timedelta(days=int(count.split(' ')[0]) - 1)).strftime('%Y-%m-%d')
        tag = event.find_next('i')
        new_tag = False
        if tag is not None:
            if tag.getText() == 'New':
                new_tag = True
        url = event.find_next('a').get('href')
        content_id = get_content_id_from_url(url)
        thumbnail = event.find_next('img').get('src')
        # description = get_description(url)
        description = ''
        if content_id not in old_events:
            if new_tag:
                web_hook_data = WebHookData(title=title, url=url, description=description, thumbnail=thumbnail,
                                            data_type="event", date=deadline if deadline != '-' else '상시')
                post_to_webhook(url=web_hook_url, data=web_hook_data.to_json())
            added = get_date()
        else:
            added = old_events[content_id]['added'] if 'added' in old_events[content_id] else get_date()
        events[content_id] = {'title': title, 'deadline': deadline, 'count': count, 'url': url, 'thumbnail': thumbnail,
                              'description': description, 'content_id': content_id, 'new_tag': new_tag, 'added': added}

    with open(os.path.join(BASE_DIR, 'news', 'kr_event.json'), 'w+', encoding='utf-8') as json_file:
        json.dump(events, json_file, ensure_ascii=False, indent='\t')
