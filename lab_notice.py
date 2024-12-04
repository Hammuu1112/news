import json
import os

import requests
from bs4 import BeautifulSoup

from utils import get_content_id_from_url, get_description, get_date, WebHookData, post_to_webhook

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def lab_notice(web_hook_url: str):
    with open(os.path.join(BASE_DIR, 'news', 'lab_notice.json'), 'r', encoding='utf-8') as file:
        old_notices: dict = json.load(file)
    response = requests.request(method='get', url='https://blackdesert.pearlabyss.com/GlobalLab/ko-KR/News/Notice?_categoryNo=1',
                                headers={'Accept-Language': 'ko-KR,ko;q=0.9'})
    response.encoding = None
    html = response.content
    soup = BeautifulSoup(html, 'html.parser')
    data = soup.select('#wrap > div > section > article > div.board_wrap > ul')[0]
    table = data.findAll('li')

    notices = {}
    for item in table:
        # title = item.find_next('strong').find_next('em').next_sibling.split(' (최종 수정')[0].strip()
        title = item.find_next('p', {'class', 'title'}).getText().split(' (최종 수정')[0].strip()
        date = item.find_next('div', {'class', 'info'}).find_next('span', {'class', 'date'}).getText()
        desc = item.find_next('div', {'class', 'info'}).find_next('span', {'class', 'thum_cate'}).getText()
        url = item.find_next('a').get('href')
        content_id = get_content_id_from_url(url)
        thumbnail = item.find_next('img').get('src')
        description = get_description(url)
        if content_id not in old_notices:
            web_hook_data = WebHookData(title=title, url=url, description=desc, thumbnail=thumbnail, data_type="lab",
                                        date=date)
            post_to_webhook(url=web_hook_url, data=web_hook_data.to_json())
            added = get_date()
        else:
            added = old_notices[content_id]['added'] if 'added' in old_notices[content_id] else get_date()
        notices[content_id] = {'title': title, 'date': date, 'url': url, 'thumbnail': thumbnail, 'desc': desc,
                               'description': description, 'content_id': content_id, 'added': added}

    with open(os.path.join(BASE_DIR, 'news', 'lab_notice.json'), 'w+', encoding='utf-8') as json_file:
        json.dump(notices, json_file, ensure_ascii=False, indent='\t')
