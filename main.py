import redis
import requests
import queue
import threading
import time
import atexit

from urllib import parse
from config import *
from logger import logger

from proxy_source import PROXY_SOURCE_LIST

headers={
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
}

requests.adapters.DEFAULT_RETRIES = 5
s = requests.session()
s.keep_alive = False

def fetch_ips():
    http_list = []
    https_list = []
    for get_func in PROXY_SOURCE_LIST:
        http, https = get_func()
        http_list = http_list + http
        https_list = https_list + https
    return (http_list, https_list)

def check_ip(proxy):
    # logger.info('验证: {}'.format(proxy))
    try:
        if is_proxy_available(proxy):
            url_info = parse.urlparse(proxy)
            if (url_info.scheme == 'http'):
                red.sadd(REDIS_NAME_HTTP, proxy)
                logger.info('{} 已收录..'.format(proxy))
            elif (url_info.scheme == 'https'):
                red.sadd(REDIS_NAME_HTTPS, proxy)
                logger.info('{} 已收录..'.format(proxy))
    except Exception as e:
        logger.error(e)

def check_ips():
    while True:
        job = ip_q.get()
        check_ip(job)
        ip_q.task_done()

def do_fetch():
    # 重置 TTL
    red.setex(PROXY_PROTECT, PROTECT_SEC, 'PROXY_PROTECT')
    red.setex(PROXY_REFRESH, REFRESH_SEC, 'PROXY_REFRESH')

    logger.info('正在获取代理地址...')
    http_list, https_list = fetch_ips()
    # print(ip_list)
    logger.info('成功获取 {} 个 http 代理地址和 {} 个 https 代理地址'.format(len(http_list), len(https_list)))
    logger.info('验证代理...')
    for ip in http_list:
        ip_q.put(ip)
    for ip in https_list:
        ip_q.put(ip)

    ip_q.join()
    logger.info('验证完成')

def proxy_fetch():
    while True:
        protect_ttl = red.ttl(PROXY_PROTECT)
        refresh_ttl = red.ttl(PROXY_REFRESH)

        http_count = len(red.smembers(REDIS_NAME_HTTP))
        logger.info('当前 http 代理数量：{}'.format(http_count))
        if http_count < PROXY_LOW and protect_ttl <= 0:
            logger.info('http 代理池存量低了，需要补充些代理... (*゜ー゜*)')
            do_fetch()
        elif http_count < PROXY_EXHAUST:
            logger.info('http 代理池即将耗尽啦，需要立即补充些代理... Σ( ° △ °|||)')
            do_fetch()
        elif http_count < PROXY_LOW and protect_ttl > 0:
            logger.info('http 代理池存量有点低，但尚在保护期，剩余保护时间：{}... O__O'.format(protect_ttl))
            do_fetch()
        elif refresh_ttl <= 0:
            logger.info('http 代理池太久没更新啦，补充些新鲜代理... ლ(╹◡╹ლ)')
            do_fetch()
        else:
            logger.info('库存情况良好... (๑•̀ㅂ•́)و✧'.format(http_count))

        https_count = len(red.smembers(REDIS_NAME_HTTPS))
        logger.info('当前 https 代理数量：{}'.format(https_count))
        if https_count < PROXY_LOW and protect_ttl <= 0:
            logger.info('https 代理池存量低了，需要补充些代理... (*゜ー゜*)')
            do_fetch()
        elif https_count < PROXY_EXHAUST:
            logger.info('https 代理池即将耗尽啦，需要立即补充些代理... Σ( ° △ °|||)')
            do_fetch()
        elif https_count < PROXY_LOW and protect_ttl > 0:
            logger.info('https 代理池存量有点低，但尚在保护期，剩余保护时间：{}... O__O'.format(protect_ttl))
            do_fetch()
        elif refresh_ttl <= 0:
            logger.info('https 代理池太久没更新啦，补充些新鲜代理... ლ(╹◡╹ლ)')
            do_fetch()
        else:
            logger.info('库存情况良好... (๑•̀ㅂ•́)و✧'.format(https_count))

        time.sleep(LOOP_DELAY)


# 检测一个特定的代理是否有效
def is_proxy_available(proxy, timeout=10):
    url_info = parse.urlparse(proxy)
    if url_info.scheme == 'http':
        validate_url = VALIDATE_URL_HTTP
        proxies = {'http': proxy}
    elif url_info.scheme == 'https':
        validate_url = VALIDATE_URL_HTTPS
        proxies = {'https': proxy}
    try:
        s.get(validate_url, proxies=proxies, timeout=timeout, headers=headers, allow_redirects=False)
        return True
    except Exception as e:
        # logger.error(e)
        return False


def do_check():
    proxy_set = red.smembers(REDIS_NAME_HTTP)
    for proxy in proxy_set:
        if is_proxy_available(proxy, 15):
            continue
        # 到这里说明代理不可用
        red.srem(REDIS_NAME_HTTP, proxy)

    proxy_set = red.smembers(REDIS_NAME_HTTPS)
    for proxy in proxy_set:
        if is_proxy_available(proxy, 5):
            continue
        # 到这里说明代理不可用
        red.srem(REDIS_NAME_HTTPS, proxy)

    return (len(red.smembers(REDIS_NAME_HTTP)), len(red.smembers(REDIS_NAME_HTTPS)))

def proxy_check():
    while True:
        logger.info('检查库存代理质量...')
        http_count, https_count = do_check()
        logger.info('检查完成，存活 http 代理数 {}，存活 https 代理数 {}..'.format(http_count, https_count))
        time.sleep(CHECK_INTERVAL)

# 退出进程，关闭 redis 连接
@atexit.register
def atexit_func():
    logger.info('关闭 Redis 连接...')
    red.close()
    logger.info('关闭成功')

if __name__ == '__main__':
    logger.info('连接 Redis...')
    red = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True)
    logger.info('连接成功')

    # 设置 ttl
    red.setex(PROXY_PROTECT, PROTECT_SEC, 'PROXY_PROTECT')
    red.setex(PROXY_REFRESH, REFRESH_SEC, 'PROXY_REFRESH')

    # 启动自检线程
    check_thd = threading.Thread(target=proxy_check)
    check_thd.setDaemon(True)
    check_thd.start()

    # 启动抓取线程
    fetch_thd = threading.Thread(target=proxy_fetch)
    fetch_thd.setDaemon(True)
    fetch_thd.start()

    # 待检测 ip 队列
    ip_q = queue.Queue()

    # 启动 40 个爬虫进程
    crawler_thds = []
    for i in range(40):
        t = threading.Thread(target=check_ips)
        t.setDaemon(True)
        t.start()
        crawler_thds.append(t)

    while True:
        if not check_thd.is_alive():
            logger.error('自检线程已挂..重启中..')
            check_thd.start()
        if not fetch_thd.is_alive():
            logger.error('抓取线程已挂..重启中..')
            fetch_thd.start()
        dead_thd = []
        for t in crawler_thds:
            if not t.is_alive():
                dead_thd.append(t)
        if len(dead_thd) > 0:
            logger.error('{} 个爬虫进程已挂..重启中..'.format(len(dead_thd)))
            for t in dead_thd:
                t.start()

        time.sleep(60)
