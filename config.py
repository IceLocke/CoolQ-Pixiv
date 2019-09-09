from nonebot.default_config import *
from datetime import timedelta

SESSION_EXPIRE_TIMEOUT = timedelta(seconds=10)
SUPERUSERS = {}
COMMAND_START = {'/'}

# 此处设置你的 CQHttpApi 监听的地址
HOST = '127.0.0.1'
PORT = 8080