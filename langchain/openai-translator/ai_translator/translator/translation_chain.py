from langchain.chat_models import ChatOpenAI
from langchain.llms import ChatGLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from utils import LOG

class TranslationChain:
    def __init__(self, 
                 model_name: str = "gpt-3.5-turbo", 
                 glm_endpoint_url: str = "http://127.0.0.1:8000", 
                 verbose: bool = True):

        # 为了翻译结果的稳定性，将 temperature 设置为 0
        if model_name == 'chatglm-6b': 
            template = """
            你是一个翻译专家。将以下所有的 {source_language} 翻译为 {target_language}。
            文本如下：{text}"""
            prompt = PromptTemplate(template=template, input_variables=["source_language", "target_language", "text"])
            chat = ChatGLM(endpoint_url=glm_endpoint_url, temperature=0)
            self.chain = LLMChain(llm=chat, prompt=prompt, verbose=verbose)
        else:  # openai gpt-3.5-turbo
            # 翻译任务指令始终 System 角色承担
            template = (
                """You are a translation expert, proficient in various languages. \n
                Translates {source_language} to {target_language}."""
            )
            system_message_prompt = SystemMessagePromptTemplate.from_template(template)

            # 待翻译文本由 Human 角色输入
            human_template = "{text}"
            human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

            # 使用 System 和 Human 角色的提示模板构造 ChatPromptTemplate
            chat_prompt_template = ChatPromptTemplate.from_messages(
                [system_message_prompt, human_message_prompt]
            )

            chat = ChatOpenAI(model_name=model_name, temperature=0, verbose=verbose)
            self.chain = LLMChain(llm=chat, prompt=chat_prompt_template, verbose=verbose)

    def run(self, text: str, source_language: str, target_language: str) -> (str, bool):
        result = ""
        try:
            result = self.chain.run({
                "text": text,
                "source_language": source_language,
                "target_language": target_language,
            })
        except Exception as e:
            LOG.error(f"An error occurred during translation: {e}")
            return result, False

        return result, True