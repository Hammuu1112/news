import json
import os

import requests
from bs4 import BeautifulSoup

from utils import get_content_id_from_url, get_description, get_date, WebHookData, post_to_webhook

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def kr_notice(web_hook_url: str):
    with open(os.path.join(BASE_DIR, 'news', 'kr_notice.json'), 'r', encoding='utf-8') as file:
        old_notices: dict = json.load(file)
    response = requests.request(method='get', url='https://www.kr.playblackdesert.com/ko-KR/News/Notice?boardType=1')
    response.encoding = None
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    print(soup.select('#wrap > div > div.container > article > div.tab_container > div > div.thumb_nail_area > ul'))
    data = soup.select('#wrap > div > div.container > article > div.tab_container > div > div.thumb_nail_area > ul')[0]
    table = data.findAll('li')

    notices = {}
    for item in table:
        title = item.find_next('strong').find_next('span', {'class', 'line_clamp'}).getText().split('(최종')[0].strip()
        date = item.find_next('strong').find_next('span', {'class', 'date'}).getText()
        desc = item.find_next('strong').find_next('span', {'class', 'desc'}).getText()
        url = item.find_next('a').get('href')
        content_id = get_content_id_from_url(url)
        thumbnail = item.find_next('img').get('src')
        description = get_description(url)
        if content_id not in old_notices:
            web_hook_data = WebHookData(title=title, url=url, description=desc, thumbnail=thumbnail, data_type="notice",
                                        date=date)
            post_to_webhook(url=web_hook_url, data=web_hook_data.to_json())
            added = get_date()
        else:
            added = old_notices[content_id]['added'] if 'added' in old_notices[content_id] else get_date()
        notices[content_id] = {'title': title, 'date': date, 'url': url, 'thumbnail': thumbnail, 'desc': desc,
                               'description': description, 'content_id': content_id, 'added': added}

    with open(os.path.join(BASE_DIR, 'news', 'kr_notice.json'), 'w+', encoding='utf-8') as json_file:
        json.dump(notices, json_file, ensure_ascii=False, indent='\t')
