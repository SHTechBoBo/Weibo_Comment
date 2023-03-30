import json
import os
import requests
import random
import time
import concurrent.futures
import re
from datetime import datetime

# https://m.weibo.cn/

TOPIC_PATH = "./topics"

# PROXY = {
#     'http': 'http://127.0.0.1:7890',
#     'https': 'http://127.0.0.1:7890',
# }

# USER_AGENT_LIST = [
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36",
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36"
# ]


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
    sleep_time = random.uniform(1, 5)
    # print("Wait {} Seconds...".format(sleep_time))
    time.sleep(sleep_time - random.random())

    # 请求网站数据
    response = requests.get(url=url, headers=get_header())

    # 请求成功返回
    if response.status_code == 200:
        # print("Request Success!".format(url))
        return response
    # 请求失败报错
    else:
        raise Exception("Request Fail: {}".format(url))


def get_topic(topic: str):
    topic_api = "https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{" \
                "}&page_type=searchall&page={} "

    # 存放讨论的编号
    id_list = []
    start_time = datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S')
    print("=== Topic {} Begin At {} ===".format(topic, start_time))
    page = -1
    while True:
        page += 1
        response = get_request(topic_api.format(topic, page))
        ids = re.findall(r'mid=([0-9]+)', response.text)
        if len(ids) == 0 or len(id_list) >= 100:
            break
        id_list.extend(ids)

    id_list = list(set(id_list))
    print("Topic {} Collect {} Discussions In ALL.".format(topic, len(id_list)))
    data_dic = get_comment(topic, id_list)
    data_dic["start_time"] = start_time
    return data_dic


def get_comment(topic: str, id_list: list):
    comment_api = "https://m.weibo.cn/api/comments/show?id={}&page={}"
    comment_dic = {}
    print("*** Start Collecting Comments For Topic {} ***".format(topic))
    for id_ in id_list:
        page = -1
        while True:
            page += 1
            response = get_request(comment_api.format(id_, page))
            try:
                for info in response.json()["data"]["data"]:
                    text = info["text"]
                    source = info["source"]
                    user = info["user"]["screen_name"]
                    comment_time = info["created_at"]
                    if text == "转发微博" or user in comment_dic:
                        continue
                    comment_dic[user] = {"source": source, "time": comment_time, "text": text}
            except (json.decoder.JSONDecodeError, KeyError):
                break
        print("Topic {} Discussions ID {} Finish With {} Comments.".format(topic, id_, len(comment_dic)))
    print("*** Topic {} Finish With {} Comments ***".format(topic, len(comment_dic)))
    return comment_dic


def process_file(file: str):
    # 创建文件夹
    dir_path = os.path.join("./comments", file.split(".")[0])
    os.makedirs(dir_path, exist_ok=True)
    # 读取原始json文件
    with open(os.path.join(TOPIC_PATH, file), "r", encoding='utf-8') as in_file:
        print("File:{} Start".format(os.path.join(TOPIC_PATH, file)))
        record = json.load(in_file)
    for title in record:
        data = get_topic(title)
        data["hot"] = record[title]["hot"]
        # 获取评论并写入json
        with open(os.path.join(dir_path, "{}.json".format(title)), 'w', encoding='utf-8') as out_file:
            out_file.write(json.dumps(data, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    # 读取所有json文件
    record_jsons = sorted(list(os.walk(TOPIC_PATH))[0][2:][0], reverse=True)

    # for file_ in record_jsons:
    #     process_file(file_)

    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        executor.map(process_file, record_jsons)
