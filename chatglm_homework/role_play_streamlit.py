"""
作业2
一个简单的demo，调用CharacterGLM实现角色扮演，调用ChatGLM生成所需的prompt。

依赖：
pyjwt
requests
streamlit
zhipuai
python-dotenv

运行方式：
```bash
streamlit run characterglm_api_demo_streamlit.py
```

点击“生成一轮对话”。第一次点击时，会调用glm生成人设，再生成一轮对话。使用README.md中的人设，可以生成对话。点击“保存文件”，在本地保存文件。
"""

import os
import itertools
from typing import Iterator, Optional

import streamlit as st
from dotenv import load_dotenv

# 通过.env文件设置环境变量
# reference: https://github.com/theskumar/python-dotenv
load_dotenv()

import api
from api import (
    generate_chat_scene_prompt,
    generate_role_appearance,
    get_characterglm_response,
    generate_role_persona,
)
from data_types import TextMsg, ImageMsg, TextMsgList, MsgList, filter_text_msg

st.set_page_config(page_title="CharacterGLM API Demo", page_icon="🤖", layout="wide")
debug = os.getenv("DEBUG", "").lower() in ("1", "yes", "y", "true", "t", "on")


def update_api_key(key: Optional[str] = None):
    if debug:
        print(
            f'update_api_key. st.session_state["API_KEY"] = {st.session_state["API_KEY"]}, key = {key}'
        )
    key = key or st.session_state["API_KEY"]
    if key:
        api.API_KEY = key


# 设置API KEY
api_key = st.sidebar.text_input(
    "API_KEY",
    value=os.getenv("API_KEY", ""),
    key="API_KEY",
    type="password",
    on_change=update_api_key,
)
update_api_key(api_key)


# 初始化
if "history" not in st.session_state:
    st.session_state["history"] = []
if "swapped_history" not in st.session_state:
    st.session_state["swapped_history"] = []
if "meta" not in st.session_state:
    st.session_state["meta"] = {
        "bot_name": "",
        "bot_fragment": "",
        "bot_info": "",
        "user_name": "",
        "user_fragment": "",
        "user_info": "",
    }


def init_session():
    st.session_state["history"] = []
    st.session_state["swapped_history"] = []


# 4个输入框，设置meta的4个字段
meta_labels = {
    "bot_name": "角色1",
    "bot_fragment": "角色1信息",
    "user_name": "角色2",
    "user_fragment": "角色2信息",
}

# 2x2 layout
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(
            label="角色1",
            key="bot_name",
            on_change=lambda: st.session_state["meta"].update(
                bot_name=st.session_state["bot_name"]
            ),
            help="模型所扮演的角色1的名字，不可以为空",
        )
        st.text_area(
            label="角色1信息",
            key="bot_fragment",
            on_change=lambda: st.session_state["meta"].update(
                bot_fragment=st.session_state["bot_fragment"]
            ),
            help="角色1的详细人设信息，不可以为空",
        )

    with col2:
        st.text_input(
            label="角色2",
            key="user_name",
            on_change=lambda: st.session_state["meta"].update(
                user_name=st.session_state["user_name"]
            ),
            help="模型所扮演的角色1的名字，不可以为空",
        )
        st.text_area(
            label="角色2信息",
            key="user_fragment",
            on_change=lambda: st.session_state["meta"].update(
                user_fragment=st.session_state["user_fragment"]
            ),
            help="角色2的详细人设信息，不可以为空",
        )


def verify_meta() -> bool:
    # 检查`角色1,2`和`角色1,2人设`是否空，若为空，则弹出提醒
    if (
        st.session_state["meta"]["bot_name"] == ""
        or st.session_state["meta"]["bot_fragment"] == ""
        or st.session_state["meta"]["user_name"] == ""
        or st.session_state["meta"]["user_fragment"] == ""
    ):
        st.error("角色名和角色人设不能为空")
        return False
    else:
        return True


def save_to_file():
    """保存到文件"""
    if not verify_meta():
        return

    personas = "\n".join(
        [
            'bot_name:',
            st.session_state["meta"]["bot_name"],
            'bot_info:',
            st.session_state["meta"]["bot_info"],
            '\nuser_name:',
            st.session_state["meta"]["user_name"],
            'user_info:',
            st.session_state["meta"]["user_info"],
        ]
    )

    text_messages = filter_text_msg(st.session_state["history"])
    if text_messages:
        # 若有对话历史，则结合角色人设和对话历史
        # file_content = personas + '\n\n' + str(text_messages)
        # 让对话更可读
        conversation = ''
        for item in text_messages:
            role = item['role']
            content = item['content'].strip()  # 去除内容两侧的空白字符（包括换行符）
            if content:  # 如果内容不为空
                if role == 'user':
                    conversation += '\n' + st.session_state['meta']['user_name'] + '\n'
                elif role == 'assistant':
                    conversation += '\n' + st.session_state['meta']['bot_name'] + '\n'
                else:
                    conversation += f"\n{role}:\n"
                # 打印一个空行，作为不同发言之间的分隔
                conversation += content + '\n'

        file_content = (
            '===人设===\n\n' + personas + '\n\n===对话历史===\n\n' + conversation
        )
    else:
        # 若没有对话历史，则保存角色人设
        file_content = '===人设===\n\n' + personas

    if not file_content:
        st.error("生成文件")
        return

    print(f"\n\nfile_content: {file_content}")

    # 新建chat_history.txt, 将image_prompt保存到文件中
    with open("chat_history.txt", "w", encoding="utf-8") as f:
        f.write(file_content)

    # n_retry = 3
    # st.markdown("正在生成图片，请稍等...")
    # for i in range(n_retry):
    #     try:
    #         img_url = generate_cogview_image(image_prompt)
    #     except Exception as e:
    #         if i < n_retry - 1:
    #             st.error("遇到了一点小问题，重试中...")
    #         else:
    #             st.error("又失败啦，点击【生成图片】按钮可再次重试")
    #             return
    #     else:
    #         break
    # img_msg = ImageMsg({"role": "image", "image": img_url, "caption": image_prompt})
    # # 若history的末尾有图片消息，则替换它，（重新生成）
    # # 否则，append（新增）
    # while (
    #     st.session_state["history"]
    #     and st.session_state["history"][-1]["role"] == "image"
    # ):
    #     st.session_state["history"].pop()
    # st.session_state["history"].append(img_msg)
    # st.rerun()


button_labels = {
    "gen_info": "生成人设",
    "clear_meta": "清空人设",
    "gen_exchange": "生成一轮对话",
    "clear_history": "清空对话历史",
    "save_file": "保存文件",
}
if debug:
    button_labels.update(
        {
            "show_api_key": "查看API_KEY",
            "show_meta": "查看meta",
            "show_history": "查看历史",
        }
    )

# 在同一行排列按钮
with st.container():
    n_button = len(button_labels)
    cols = st.columns(n_button)
    button_key_to_col = dict(zip(button_labels.keys(), cols))

    with button_key_to_col["clear_meta"]:
        clear_meta = st.button(button_labels["clear_meta"], key="clear_meta")
        if clear_meta:
            st.session_state["meta"] = {
                "bot_name": "",
                "bot_fragment": "",
                "bot_info": "",
                "user_name": "",
                "user_fragment": "",
                "user_info": "",
            }
            st.rerun()

    with button_key_to_col["clear_history"]:
        clear_history = st.button(button_labels["clear_history"], key="clear_history")
        if clear_history:
            init_session()
            st.rerun()

    with button_key_to_col["gen_info"]:
        gen_info = st.button(button_labels["gen_info"], key="gen_info")

    with button_key_to_col["gen_exchange"]:
        gen_exchange = st.button(button_labels["gen_exchange"], key="gen_exchange")

    with button_key_to_col["save_file"]:
        save_file = st.button(button_labels["save_file"], key="save_file")

    if debug:
        with button_key_to_col["show_api_key"]:
            show_api_key = st.button(button_labels["show_api_key"], key="show_api_key")
            if show_api_key:
                print(f"API_KEY = {api.API_KEY}")

        with button_key_to_col["show_meta"]:
            show_meta = st.button(button_labels["show_meta"], key="show_meta")
            if show_meta:
                print(f"meta = {st.session_state['meta']}")
                # test
                print('swapped meta =')
                print(
                    {
                        'bot_name': st.session_state['meta']['user_name'],
                        'bot_info': st.session_state['meta']['user_info'],
                        'user_name': st.session_state['meta']['bot_name'],
                        'user_info': st.session_state['meta']['bot_info'],
                    }
                )

        with button_key_to_col["show_history"]:
            show_history = st.button(button_labels["show_history"], key="show_history")
            if show_history:
                print(f"history = {st.session_state['history']}")
                print(f"swapped_history = {st.session_state['swapped_history']}")


# 展示对话历史
for msg in st.session_state["history"]:
    if msg["role"] == "user":
        with st.chat_message(name="user", avatar="user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message(name="assistant", avatar="assistant"):
            st.markdown(msg["content"])
    elif msg["role"] == "image":
        with st.chat_message(name="assistant", avatar="assistant"):
            st.image(msg["image"], caption=msg.get("caption", None))
    else:
        raise Exception("Invalid role")


def gen_bot_and_user_info():
    """生成bot和user的persona"""
    bot_info = "".join(generate_role_persona(st.session_state["meta"]["bot_fragment"]))
    st.session_state["meta"].update(bot_info=bot_info)
    user_info = "".join(
        generate_role_persona(st.session_state["meta"]["user_fragment"])
    )
    st.session_state["meta"].update(user_info=user_info)


if gen_info:
    gen_bot_and_user_info()

if save_file:
    save_to_file()

# 对话行
with st.chat_message(name="user", avatar="user"):
    input_placeholder = st.empty()
with st.chat_message(name="assistant", avatar="assistant"):
    message_placeholder = st.empty()


def output_stream_response(response_stream: Iterator[str], placeholder):
    """将get_characterglm_response()的输出打印到placeholder"""
    content = ""
    for content in itertools.accumulate(response_stream):
        placeholder.markdown(content)
    return content


def gen_response_1():
    """生成机器（角色1）的回答"""
    response_stream = get_characterglm_response(
        filter_text_msg(st.session_state["history"]),
        meta=st.session_state["meta"],
    )
    bot_response = output_stream_response(response_stream, message_placeholder)
    print('gen_response_1():', bot_response)

    if not bot_response:
        message_placeholder.markdown("生成出错")
        st.session_state["history"].pop()
        st.session_state["swapped_history"].pop()
    else:
        st.session_state["history"].append(
            TextMsg({"role": "assistant", "content": bot_response})
        )
        st.session_state["swapped_history"].append(
            TextMsg({"role": "user", "content": bot_response})
        )


def gen_response_2():
    """生成用户（角色2）的回答"""
    response_stream = get_characterglm_response(
        filter_text_msg(st.session_state["swapped_history"]),
        meta={
            'bot_name': st.session_state['meta']['user_name'],
            'bot_info': st.session_state['meta']['user_info'],
            'user_name': st.session_state['meta']['bot_name'],
            'user_info': st.session_state['meta']['bot_info'],
        },
    )
    bot_response = output_stream_response(response_stream, input_placeholder)
    print('gen_response_2():', bot_response)

    if not bot_response:
        input_placeholder.markdown("生成出错")
        st.session_state["history"].pop()
        st.session_state["swapped_history"].pop()
    else:
        st.session_state["history"].append(
            TextMsg({"role": "user", "content": bot_response})
        )
        st.session_state["swapped_history"].append(
            TextMsg({"role": "assistant", "content": bot_response})
        )


if gen_exchange:
    if not verify_meta():
        st.error("verify_meta() failed")
    if not api.API_KEY:
        st.error("未设置API_KEY")

    if (
        st.session_state["meta"]['bot_info'] == ''
        or st.session_state["meta"]['user_info'] == ''
    ):
        gen_bot_and_user_info()

    if len(st.session_state["history"]) == 0:
        # 第一轮对话
        # 对话的第一句话
        FIRST_LINE = (
            '你好，见到你很高兴。我们做个自我介绍吧。我是'
            + st.session_state["meta"]['user_name']
            + '。'
            + st.session_state["meta"]['user_info']
        )

        input_placeholder.markdown(FIRST_LINE)
        st.session_state["history"].append(
            TextMsg({"role": "user", "content": FIRST_LINE})
        )
        st.session_state["swapped_history"].append(
            TextMsg({"role": "assistant", "content": FIRST_LINE})
        )
        gen_response_1()
    else:
        # 之后的对话
        gen_response_2()
        gen_response_1()

    # response_stream = get_characterglm_response(
    #     filter_text_msg(st.session_state["swapped_history"]),
    #     meta={
    #         'bot_name': st.session_state['meta']['user_name'],
    #         'bot_info': st.session_state['meta']['user_info'],
    #         'user_name': st.session_state['meta']['bot_name'],
    #         'user_info': st.session_state['meta']['bot_info'],
    #     },
    # )
    # bot_response = output_stream_response(response_stream, message_placeholder)


def start_chat():
    query = st.chat_input("开始对话吧")
    if not query:
        return
    else:
        if not verify_meta():
            return
        if not api.API_KEY:
            st.error("未设置API_KEY")

        input_placeholder.markdown(query)
        st.session_state["history"].append(TextMsg({"role": "user", "content": query}))
        st.session_state["swapped_history"].append(
            TextMsg({"role": "assistant", "content": query})
        )

        response_stream = get_characterglm_response(
            filter_text_msg(st.session_state["history"]), meta=st.session_state["meta"]
        )
        bot_response = output_stream_response(response_stream, message_placeholder)
        if not bot_response:
            message_placeholder.markdown("生成出错")
            st.session_state["history"].pop()
            st.session_state["swapped_history"].pop()
        else:
            st.session_state["history"].append(
                TextMsg({"role": "assistant", "content": bot_response})
            )
            st.session_state["swapped_history"].append(
                TextMsg({"role": "user", "content": bot_response})
            )


start_chat()
