import json
import os

import requests
from bs4 import BeautifulSoup

from utils import get_content_id_from_url, get_description, WebHookData, post_to_webhook

start_with = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '[']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def lab_update(web_hook_url: str):
    with open(os.path.join(BASE_DIR, 'news', 'lab_update.json'), 'r', encoding='utf-8') as file:
        old_updates: dict = json.load(file)
    response = requests.request(method='get', url='https://www.global-lab.playblackdesert.com/News/Notice?boardType=2',
                               headers={'Accept-Language': 'ko-KR,ko;q=0.9'})
    response.encoding = None
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    data = soup.select('#wrap > div > div.container > article > div.tab_container > div > div.thumb_nail_area > ul')[0]
    table = data.findAll('li')

    updates = {}
    for item in table:
        title = item.find_next('strong').find_next('em').getText().split(' (최종 수정')[0].strip()
        date = item.find_next('strong').find_next('span', {'class', 'date'}).getText()
        desc = item.find_next('strong').find_next('span', {'class', 'desc'}).getText()
        url = item.find_next('a').get('href')
        content_id = get_content_id_from_url(url)
        thumbnail = item.find_next('img').get('src')
        description = get_description(url)
        if content_id not in old_updates:
            web_hook_data = WebHookData(title=title, url=url, description=desc, thumbnail=thumbnail, data_type="lab",
                                        date=date)
            post_to_webhook(url=web_hook_url, data=web_hook_data.to_json())
        updates[content_id] = {'title': title, 'date': date, 'url': url, 'thumbnail': thumbnail, 'desc': desc,
                               'description': description, 'content_id': content_id}

    with open(os.path.join(BASE_DIR, 'news', 'lab_update.json'), 'w+', encoding='utf-8') as json_file:
        json.dump(updates, json_file, ensure_ascii=False, indent='\t')
