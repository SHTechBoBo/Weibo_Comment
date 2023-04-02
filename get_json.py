import json
import os
import requests
import random
import time
import concurrent.futures
from bs4 import BeautifulSoup
import re
from datetime import datetime
import subprocess
import threading

PROXY = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
}

url_list =[
    "https://weibocomment-production.up.railway.app/comments/20230324",
    "https://weibocomment-production.up.railway.app/comments/20230325",
    "https://weibocomment-production.up.railway.app/comments/20230326",
    "https://weibocomment-production.up.railway.app/comments/20230327",
    "https://weibocomment-production.up.railway.app/comments/20230328",
    "https://weibocomment-production.up.railway.app/comments/20230329",
    "https://weibocomment-production.up.railway.app/comments/20230330",
]


def get_header():
    chrome_version = random.randint(80, 90)
    build_version = random.randint(4100, 4200)
    patch_version = random.randint(100, 150)
    user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/" \
                 f"{chrome_version}.0.{build_version}.{patch_version} Safari/537.36 "
    return {"User-Agent": user_agent,
            "Referer": "https://m.weibo.cn/"}


def get_request(url: str):
    # 随机暂停1-5秒
    sleep_time = random.uniform(3, 5)
    # print("Wait {} Seconds...".format(sleep_time))
    time.sleep(sleep_time - random.random())

    # 请求网站数据
    response = requests.get(url=url, proxies=PROXY, headers=get_header())

    # 请求成功返回
    if response.status_code == 200:
        # print("Request Success!".format(url))
        return response
    # 请求失败报错
    else:
        raise Exception("Request Fail: {}".format(url))


def process_link(url, link, dir_path):
    href = url + "/" + link["href"]
    name = link.text
    result = get_request(href).json()
    with open("{}/{}".format(dir_path, name), "w", encoding='utf-8') as out_file:
        out_file.write(json.dumps(result, indent=4, ensure_ascii=False))


def process_links(url, links, dir_path):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        tasks = []
        for link in links:
            task = executor.submit(process_link, url, link, dir_path)
            tasks.append(task)
        for task in tasks:
            task.result()


def process_url(url):
    response = get_request(url)
    links = BeautifulSoup(response.text, 'html.parser').find_all("a")
    dir_path = "./comments/{}".format(url.split("/")[-1])
    os.makedirs(dir_path, exist_ok=True)
    process_links(url, links, dir_path)


if __name__ == '__main__':

    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        tasks = []
        for url in url_list:
            task = executor.submit(process_url, url)
            tasks.append(task)
        for task in tasks:
            task.result()
