import streamlit as st
import time
import crawl
import re

# 创建一个表单
with st.form("download_form"):
    key_input = st.text_input("微博热门话题关键词:")
    # 将提交按钮放在表单内部
    submit_button = st.form_submit_button("获取评论")

# 当提交按钮被按下时
if submit_button:
    # 如果输入不为空
    if key_input:
        # 显示开始爬取的信息
        st.success(f"爬取中......")
        # 记录开始时间
        start_time = time.time()

        # 调用爬虫函数下载json
        comment_num, file_path = crawl.topic_crawl(key_input)

        # 记录结束时间
        end_time = time.time()
        # 计算耗时
        elapsed_time = end_time - start_time

        # 读取压缩文件内容并创建下载按钮
        with open(file_path, "rb") as file:
            file_content = file.read()
            st.download_button(
                label="下载Json文件",
                data=file_content,
                file_name=f"{key_input}.json",
                mime="application/json"
            )

        # 显示下载成功及耗时信息
        st.success(f"爬取{comment_num}条评论成功，用时{elapsed_time:.2f}秒")

    else:
        # 如果输入为空，则显示错误信息
        st.error("请输入关键词!")

# 要运行此文件，请在终端中输入：streamlit run app.py
