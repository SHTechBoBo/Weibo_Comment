from Requester import Requester
import os
import re
import json
from datetime import datetime

topic_api = "https://m.weibo.cn/api/container/getIndex?" \
            "containerid=100103type%3D1%26q%3D{}&page_type=searchall&page={}"

comment_api_0 = "https://m.weibo.cn/comments/hotflow?id={}&mid={}&max_id_type=0"

comment_api_1 = "https://m.weibo.cn/comments/hotflow?id={}&mid={}&max_id={}&max_id_type=0"

cookie = "__bid_n=18737a371a931ac31a4207; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WWD2CwfRmnib04qQeVOTAu65NHD95QNShz4S0q7eoBRWs4DqcjK-Xy-9gSQi--Xi-zRi-zcBJvFd7tt; _T_WM=37699679165; WEIBOCN_FROM=1110006030; MLOGIN=1; FPTOKEN=mHL0R/SSBGFZUC0w+XSITVxFRzpU2ZivaWjXMTiZvJ/O2Px1pbeSp/Tg226qHK1YJSVlG/mBYj4dF6yqmQuYlqCoT7Gglxq0CuLX0DvZjskDjHCACNhtvlBsoyDON0AbUZQwD+Z4J2jkJBTZIozRRLrc9p6jEmqcfrrXyIvJ157OVIb3+B9Diavdme2Jqe89arAjGhyAai9cI6k9h30fBCW8ktJ0xa8IV+baIJ8+DfnIciCaFANJg0eOwoAngdZcZtaRDs0yh5PdM5AVyoQ4oc7NL37SmmT3dPm5BVmoKpRNehIe/YwSBKW14qO1iRLcWTqG9uE3fo5nE+gl9RoKJ+dcqoEo6OB3bSrAugnJ/I221qcmtEtX+RLrQ9P2X6lnljm8fco8TqUeefZspWuqvA==|hFzTsorBaHKS3rIuMMDOd3SIZMMDb5/jfVLaWwxKGeg=|10|fea73187455a5bfd9f7dc44671d80d9e; M_WEIBOCN_PARAMS=oid=4892209499345964&luicode=10000011&lfid=100103type%3D1%26q%3D%E4%B8%8A%E6%B5%B7%E7%A7%91%E6%8A%80%E5%A4%A7%E5%AD%A6%E8%99%90%E7%8C%AB; XSRF-TOKEN=fba0e3; SUB=_2A25JRM-gDeRhGeFK6VsW9i7OzzSIHXVqxtHorDV6PUJbktAGLUyhkW1NQ2PgTGJbrO52iooCSOk1aycJXEeXbykA; SSOLoginState=1681965040; mweibo_short_token=9fc67f650b"

proxies = {
    'http': 'http://127.0.0.1:7890',
    'https': 'http://127.0.0.1:7890',
}

Weibo_Requester = Requester(referer="https://m.weibo.cn/", sleep_time=(3, 5), proxy=proxies, cookie=cookie)


def get_topic_discussion(topic: str):
    id_list = []
    page = 0

    while True:
        response = Weibo_Requester.get_request(topic_api.format(topic, page))
        if response.status_code == 200:
            mid_list = re.findall(r'mid=([0-9]+)', response.text)

            if mid_list:
                id_list.extend(mid_list)
                id_list = list(set(id_list))
                page += 1
            else:
                break
        else:
            break

    print(id_list)
    return id_list


def get_comment(topic: str, id_list: list, max_comment: int = 1000):
    comment_dict = {}

    for id_ in id_list:
        max_id = -1

        while len(comment_dict) < max_comment:
            url = comment_api_0.format(id_, id_) if max_id == -1 else comment_api_1.format(id_, id_, max_id)

            response = Weibo_Requester.get_request(url)

            if not response or response.status_code != 200 or not max_id:
                break
            else:
                info_data = response.json().get("data", None)

                if info_data:
                    max_id = info_data.get("max_id", None)
                    data_list = info_data.get("data", None)

                    if data_list:
                        for data in data_list:
                            text = data.get("text", None)
                            source = data.get("source", None)
                            like = data.get("like_count", None)
                            time = data.get("created_at", None)

                            if text and text != "转发微博":
                                comment_dict[f"{topic}_{len(comment_dict)}"] = \
                                    {"text": text, "like": like, "source": source, "time": time}
                        print(f"Topic {topic} {id_} Complete {len(comment_dict)} Comments.")

                else:
                    break

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
    discussion_id_list = get_topic_discussion(key)
    comment_info_dict = get_comment(key, discussion_id_list, num)
    return len(comment_info_dict), download_json(key, comment_info_dict)


if __name__ == '__main__':
    topic_crawl("上海科技大学虐猫")
    # get_comment("上海科技大学虐猫", ['4876263888523423'])
    # ['4876311362801203', '4876307547030765', '4876263891928940',
    # '4876263888523423', '4876604515812274', '4876344132899661',
    # '4876263892976404', '4876278869529348', '4876319295277067',
    # '4876308583284917', '4876362076396386', '4876263133284148',
    # '4876276157124301', '4876262043289323', '4876324584558062',
    # '4876263133285274', '4876572718793180', '4876336047327373',
    # '4876307543101286', '4876295898665350', '4876333299007688',
    # '4876318150230729']
