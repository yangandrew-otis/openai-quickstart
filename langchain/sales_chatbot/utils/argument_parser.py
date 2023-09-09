import argparse

class ArgumentParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='教育销售机器人.')
        self.parser.add_argument('--enable_chat', action="store_true", help='开启模型聊天.')

    def parse_args(self):
        args = self.parser.parse_args()
        return args
