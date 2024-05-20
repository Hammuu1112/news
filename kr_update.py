import json
import os

import requests
from bs4 import BeautifulSoup

from utils import get_content_id_from_url, get_description, get_date, WebHookData, post_to_webhook

start_with = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '[']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def kr_update(major_web_hook_url: str, normal_web_hook_url: str):
    with open(os.path.join(BASE_DIR, 'news', 'kr_update.json'), 'r', encoding='utf-8') as file:
        old_updates: dict = json.load(file)
    response = requests.request(method='get', url='https://www.kr.playblackdesert.com/ko-KR/News/Notice?boardType=2')
    response.encoding = None
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    data = soup.select('#wrap > div > div.container > article > div.tab_container > div > div.thumb_nail_area > ul')[0]
    table = data.findAll('li')

    updates = {}
    for item in table:
        title = item.find_next('strong').find_next('span', {'class', 'line_clamp'}).getText().split('(최종')[0].strip()
        date = item.find_next('strong').find_next('span', {'class', 'date'}).getText()
        desc = item.find_next('strong').find_next('span', {'class', 'desc'}).getText()
        url = item.find_next('a').get('href')
        content_id = get_content_id_from_url(url)
        thumbnail = item.find_next('img').get('src')
        description = get_description(url)
        major = False
        if desc != '' and desc[0] not in start_with:
            major = True
        if content_id not in old_updates:
            web_hook_data = WebHookData(title=title, url=url, description=desc if major else '', thumbnail=thumbnail,
                                        data_type="update", date=date)
            post_to_webhook(url=normal_web_hook_url, data=web_hook_data.to_json())
            if major:
                post_to_webhook(url=major_web_hook_url, data=web_hook_data.to_json())
            dded = get_date()
        else:
            added = old_events[content_id]['added'] if 'added' in old_events[content_id] else get_date()
        updates[content_id] = {'title': title, 'date': date, 'url': url, 'thumbnail': thumbnail, 'desc': desc,
                               'description': description, 'content_id': content_id, 'major': major, 'added': added}

    with open(os.path.join(BASE_DIR, 'news', 'kr_update.json'), 'w+', encoding='utf-8') as json_file:
        json.dump(updates, json_file, ensure_ascii=False, indent='\t')
