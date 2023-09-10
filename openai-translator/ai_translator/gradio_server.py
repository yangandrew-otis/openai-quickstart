"""
启动：

$ python3 ./ai_translator/gradio_server.py --model_type OpenAIModel --openai_model gpt-3.5-turbo --openai_api_key sk-...
"""

import sys
import os
import gradio as gr

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import ArgumentParser, ConfigLoader, LOG
from model import OpenAIModel
from translator import PDFTranslator

def translation(input_file):
    LOG.debug(f"[翻译任务]\n源文件: {input_file.name}")
    output_file_path = Translator.translate_pdf(input_file.name, "markdown")
    LOG.debug(f"[翻译任务]\n输出文件: {output_file_path}")
    return output_file_path

def launch_gradio():
    iface = gr.Interface(
        fn=translation,
        title="OpenAI-Translator（英译中）",
        inputs=[
            gr.File(label="上传PDF文件"),
        ],
        outputs=[
            gr.File(label="下载md翻译文件")
        ],
        allow_flagging="never"
    )

    # iface.launch(share=True, server_name="0.0.0.0")
    iface.launch(server_name="0.0.0.0")

def initialize_translator():
    argument_parser = ArgumentParser()
    args = argument_parser.parse_arguments()
    config_loader = ConfigLoader(args.config)
    config = config_loader.load_config()

    model_name = args.openai_model if args.openai_model else config['OpenAIModel']['model']
    api_key = args.openai_api_key if args.openai_api_key else config['OpenAIModel']['api_key']
    model = OpenAIModel(model=model_name, api_key=api_key)

    # pdf_file_path = args.book if args.book else config['common']['book']
    # file_format = args.file_format if args.file_format else config['common']['file_format']

    # 实例化 PDFTranslator 类，并调用 translate_pdf() 方法
    global Translator
    Translator = PDFTranslator(model)


if __name__ == "__main__":
    # 初始化 translator
    initialize_translator()
    # 启动 Gradio 服务
    launch_gradio()
