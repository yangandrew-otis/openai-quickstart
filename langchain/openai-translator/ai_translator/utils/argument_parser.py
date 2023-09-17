import argparse

class ArgumentParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='A translation tool that supports translations in any language pair.')
        self.parser.add_argument('--config_file', type=str, default='config.yaml', help='Configuration file with model and API settings.')
        self.parser.add_argument('--model_name', type=str, choices=['gpt-3.5-turbo', 'chatglm-6b'], help='Name of the Large Language Model: gpt-3.5-turbo or chatglm-6b')
        self.parser.add_argument('--glm_endpoint_url', type=str, help='The URL of the ChatGLM-6b model URL.')
        self.parser.add_argument('--input_file', type=str, help='PDF file to translate.')
        self.parser.add_argument('--output_file_format', type=str, help='The file format of translated book. Now supporting PDF and Markdown')
        self.parser.add_argument('--source_language', type=str, help='The language of the original book to be translated.')
        self.parser.add_argument('--target_language', type=str, help='The target language for translating the original book.')

    def parse_arguments(self):
        args = self.parser.parse_args()
        return args
