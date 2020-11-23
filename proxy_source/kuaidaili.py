import requests
import time
import pandas as pd

from logger import logger

headers={
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
}

def get_kuaidaili(page=1):
    url = 'https://www.kuaidaili.com/free/inha/{}/'.format(page)

    r = requests.get(url, headers=headers)
    r.encoding = 'utf-8'

    http_list = []
    https_list = []
    try:
        df = pd.read_html(r.text)[0]
        table = df.to_dict()
        for i in table['IP']:
            host = table['IP'][i].strip()
            port = str(table['PORT'][i]).strip()
            type = table['类型'][i].strip().lower()
            if type == 'http':
                http_list.append('http://{}:{}'.format(host, port))
            elif type == 'https':
                https_list.append('https://{}:{}'.format(host, port))
    except Exception as e:
        logger.error(e)
        return ([], [])

    if page < 50:
        page += 1
        time.sleep(1)
        http, https = get_kuaidaili(page)
        http_list = http_list + http
        https_list = https_list + https

    return (http_list, https_list)