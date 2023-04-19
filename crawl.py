from Requester import Requester
import os
import re
import json
from datetime import datetime
import concurrent.futures

topic_api = "https://m.weibo.cn/api/container/getIndex?" \
            "containerid=100103type%3D1%26q%3D{}&page_type=searchall&page={}"

comment_api_0 = "https://m.weibo.cn/comments/hotflow?id={}&mid={}&max_id_type=0"

comment_api_1 = "https://m.weibo.cn/comments/hotflow?id={}&mid={}&max_id={}&max_id_type=0"

Weibo_Requester = Requester(referer="https://m.weibo.cn/", sleep_time=(1, 3))


def get_topic_discussion(topic: str, page: int):
    response = Weibo_Requester.get_request(topic_api.format(topic, page))
    if response.status_code == 200:
        mid_list = re.findall(r'mid=([0-9]+)', response.text)
        return mid_list
    return []


def get_all_discussions(topic: str, max_threads=os.cpu_count()):
    id_list = []

    # 创建一个线程池
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        # 提交任务并收集future对象
        futures = [executor.submit(get_topic_discussion, topic, page) for page in range(max_threads)]

        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                if result:
                    id_list.extend(result)
                    id_list = list(set(id_list))
                    print(f"{topic} Get {len(id_list)} Discussions")
            except Exception as e:
                print(f"Error occurred: {e}")

    return id_list


def get_comment_worker(id_, topic, max_comment, comment_dict):
    global comment_api_0, comment_api_1
    max_id = -1

    while len(comment_dict) < max_comment:
        # 根据max_id选择API模板
        url = comment_api_0.format(id_, id_) if max_id == -1 else comment_api_1.format(id_, id_, max_id)

        # 发送请求
        response = Weibo_Requester.get_request(url)

        if not response or response.status_code != 200 or not max_id:
            # 请求失败结束循环
            break
        else:
            info_data = response.json().get("data", None)

            if info_data:
                max_id = info_data.get("max_id", None)
                data_list = info_data.get("data", None)

                if data_list:
                    # 收集评论信息
                    for data in data_list:
                        text = data.get("text", None)
                        source = data.get("source", None)
                        like = data.get("like_count", None)
                        time = data.get("created_at", None)

                        # 如果为转发 则跳过
                        if text and text != "转发微博":
                            comment_dict[f"{topic}_{len(comment_dict)}"] = \
                                {"text": text, "like": like, "source": source, "time": time}
                    print(f"{topic} Collect {len(comment_dict)} Comments")
            else:
                # 请求无效结束循环
                break


def get_comment(topic: str, id_list: list, max_comment: int = 1000, max_threads=os.cpu_count()):
    comment_dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(get_comment_worker, id_, topic, max_comment, comment_dict) for id_ in id_list]
        concurrent.futures.wait(futures)

    print(f"Topic {topic} Finish With {len(comment_dict)} Comments.")
    return comment_dict


def download_json(topic: str, comment_dict: dict):
    for name, comment_info in comment_dict.items():
        # 移除"来自"字符串并更新source
        comment_info["source"] = comment_info["source"].replace("来自", "")

        # 转换时间格式并更新time
        comment_info["time"] = datetime.strptime(comment_info["time"], '%a %b %d %H:%M:%S %z %Y').strftime(
            '%Y-%m-%d %H:%M:%S')

        # 使用正则表达式清理文本中的HTML标签并更新text
        comment_info["text"] = re.sub(r'<.*?alt=(\[.*?\]).*?>', r'\1', comment_info["text"])
        comment_info["text"] = re.sub(r'<.*?>', '', comment_info["text"])

    # 将处理过的数据保存为JSON文件
    json_path = f"{topic}.json"
    with open(json_path, 'w', encoding='utf-8') as out_file:
        json.dump(comment_dict, out_file, indent=4, ensure_ascii=False)

    return os.path.abspath(json_path)


def topic_crawl(key: str, num: int = 1000):
    discussion_id_list = get_all_discussions(key)
    comment_info_dict = get_comment(key, discussion_id_list, 1000)
    return len(comment_info_dict), download_json(key, comment_info_dict)


if __name__ == '__main__':
    pass
    # key = "KPL"
    # "https://m.weibo.cn/comments/hotflow?id=4890779690467644&mid=4890779690467644&max_id_type=0"
    # discussion_id_list = get_topic_discussion(key)
    # comment_info_dict = get_comment(key, discussion_id_list, 100)
    # download_json(key, comment_info_dict)
    # with open(f"{key}.json", 'w', encoding='utf-8') as out_file:
    #     out_file.write(json.dumps(comment_info_dict, indent=4, ensure_ascii=False))


