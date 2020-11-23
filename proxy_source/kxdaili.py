import requests
import time
import pandas as pd

from logger import logger

headers={
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
}

def get_kxdaili(page=1):
    url = 'http://www.kxdaili.com/dailiip/1/{}.html'.format(page)

    r = requests.get(url, headers=headers)
    r.encoding = 'utf-8'

    http_list = []
    https_list = []
    try:
        df = pd.read_html(r.text)[0]
        table = df.to_dict()
        for i in table['IP地址']:
            host = table['IP地址'][i].strip()
            port = str(table['端口'][i]).strip()
            type = table['代理类型'][i].strip().lower()
            if 'https' in type:
                https_list.append('https://{}:{}'.format(host, port))
            if 'http,' in type:
                http_list.append('http://{}:{}'.format(host, port))
            if 'http' == type:
                http_list.append('http://{}:{}'.format(host, port))
    except Exception as e:
        logger.error(e)
        return ([], [])

    if page < 10:
        page += 1
        time.sleep(0.5)
        http, https = get_kxdaili(page)
        http_list = http_list + http
        https_list = https_list + https

    return (http_list, https_list)