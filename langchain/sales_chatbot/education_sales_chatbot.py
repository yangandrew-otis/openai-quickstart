"""
不打开大模型聊天：
$ python3 education_sales_chatbot.py

问：我想考警校
回答：这个问题我要问问领导

打开大模型聊天：
$ python3 education_sales_chatbot.py --enable_chat

问：我想考警校
回答：很好！考警校是一个很好的选择。你有什么关于考警校的问题吗？
"""

import gradio as gr
import random
import time

from typing import List

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

from utils import ArgumentParser


def initialize_sales_bot(vector_store_dir: str = "education_sales"):
    db = FAISS.load_local(vector_store_dir, OpenAIEmbeddings())
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

    global SALES_BOT
    SALES_BOT = RetrievalQA.from_chain_type(
        llm,
        retriever=db.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"score_threshold": 0.8},
        ),
    )
    # 返回向量数据库的检索结果
    SALES_BOT.return_source_documents = True

    # 是否打开大模型聊天
    argument_parser = ArgumentParser()
    args = argument_parser.parse_args()

    global ENABLE_CHAT
    ENABLE_CHAT = args.enable_chat

    return SALES_BOT


def sales_chat(message, history):
    print(f"enable_chat: {ENABLE_CHAT}")
    print(f"[message]{message}")
    print(f"[history]{history}")

    ans = SALES_BOT({"query": message})
    # 如果检索出结果，或者开了大模型聊天模式
    # 返回 RetrievalQA combine_documents_chain 整合的结果
    if ans["source_documents"] or ENABLE_CHAT:
        print(f"[result]{ans['result']}")
        print(f"[source_documents]{ans['source_documents']}")
        return ans["result"]
    # 否则输出套路话术
    else:
        return "这个问题我要问问领导"


def launch_gradio():
    demo = gr.ChatInterface(
        fn=sales_chat,
        title="教育销售",
        # retry_btn=None,
        # undo_btn=None,
        chatbot=gr.Chatbot(height=600),
    )

    demo.launch(server_name="0.0.0.0")
    # demo.launch(share=True, server_name="0.0.0.0")


if __name__ == "__main__":
    # 初始化教育销售机器人
    initialize_sales_bot()
    # 启动 Gradio 服务
    launch_gradio()
