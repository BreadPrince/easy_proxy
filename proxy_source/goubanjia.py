import requests
import pandas as pd

from logger import logger

headers={
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
}

def get_goubanjia():
    url = 'http://www.goubanjia.com/'

    r = requests.get(url, headers=headers)
    r.encoding = 'utf-8'

    http_list = []
    https_list = []
    try:
        df = pd.read_html(r.text)[0]
        table = df.to_dict()
        for i in table['IP:PORT']:
            addr = table['IP:PORT'][i].strip()
            annoymous = table['匿名度'][i].strip()
            type = table['类型'][i].strip().lower()
            if annoymous != '高匿':
                continue
            if type == 'http':
                http_list.append('http://{}'.format(addr))
            elif type == 'https':
                https_list.append('https://{}'.format(addr))
    except Exception as e:
        logger.error(e)

    return (http_list, https_list)