import json
import os
import requests
import random
import time
import concurrent.futures
import re
from datetime import datetime
import subprocess
import threading
import zipfile

WEEK = 5

# 定义一个在新线程中运行的函数
def run_subprocess():
    cmd = "python -m http.server"
    result = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE)
    # print(result.stdout)

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
    sleep_time = random.uniform(5, 10)
    # print("Wait {} Seconds...".format(sleep_time))
    time.sleep(sleep_time + random.random())

    # 请求网站数据
    # response = requests.get(url=url, proxies=PROXY, headers=get_header())
    response = requests.get(url=url, headers=get_header())

    # 请求成功返回
    if response.status_code == 200:
        # print("Request Success!".format(url))
        return response
    # 请求失败报错
    else:
        print("Request Fail: {}".format(url))
        return None


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
        if not response:
            continue
        ids = re.findall(r'mid=([0-9]+)', response.text)
        if len(ids) == 0 or len(id_list) >= 100:
            break
        id_list.extend(ids)

    id_list = list(set(id_list))
    print("Topic {} Collect {} Discussions.".format(topic, len(id_list)))
    data_dic = get_comment(topic, id_list)
    data_dic["start_time"] = start_time
    return data_dic


def get_comment(topic: str, id_list: list):
    # 第一页评论
    comment_api = "https://m.weibo.cn/comments/hotflow?id={}&mid={}&max_id_type=0"
    comment_api_ = "https://m.weibo.cn/comments/hotflow?id={}&mid={}&max_id={}&max_id_type=0"
    comment_dic = {}

    for id_ in id_list:
        max_id = -1

        while True:
            if len(comment_dic) >= 100:
                break

            # 没有后续页了
            if max_id == 0:
                break
            # 第一页
            elif max_id == -1:
                response = get_request(comment_api.format(id_, id_))
                if not response:
                    break
            # 第二页开始
            else:
                response = get_request(comment_api_.format(id_, id_, max_id))
                if not response:
                    break

            try:
                return_json = response.json()
                max_id = return_json["data"]["max_id"]
            except (json.decoder.JSONDecodeError, KeyError):
                break

            try:
                for info in return_json["data"]["data"]:
                    text = info["text"]
                    source = info["source"]
                    user = info["user"]["screen_name"]
                    comment_time = info["created_at"]
                    if text == "转发微博" or user in comment_dic:
                        continue
                    comment_dic[user] = {"source": source, "time": comment_time, "text": text}
            except (json.decoder.JSONDecodeError, KeyError):
                break

        print("Topic {} Already Finish With {} Comments.".format(topic, len(comment_dic)))

    print("=== Topic {} Finish With {} Comments. ===".format(topic, len(comment_dic)))
    return comment_dic


def process_file(file: str):
    date = file.split(".")[0]
    # 创建文件夹
    dir_path = os.path.join("./comments", date)
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

    zip_folder(dir_path, os.path.join(dir_path, date)+".zip")


def zip_folder(folder_path, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # 获取文件的相对路径，以便在ZIP文件中正确存储文件结构
                relative_path = os.path.relpath(os.path.join(root, file), folder_path)
                # 将文件添加到ZIP文件中
                zipf.write(os.path.join(root, file), relative_path)


if __name__ == '__main__':
    thread = threading.Thread(target=run_subprocess)
    thread.start()

    # 读取所有json文件
    record_jsons = sorted(list(os.walk(TOPIC_PATH))[0][2:][0], reverse=True)[7*WEEK:]

    # for file_ in record_jsons:
    #     process_file(file_)

    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        executor.map(process_file, record_jsons)



    thread.join()
