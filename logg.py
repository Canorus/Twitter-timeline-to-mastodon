import logging
import os

base = os.path.join(os.path.dirname(os.path.abspath(__file__)),'')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] >> %(message)s')
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
fileHandler = logging.FileHandler(base + 'bot.log', mode='a')
fileHandler.setFormatter(formatter)
# fileHandler = logging.handlers.RotatingFileHandler(
#     filename=base + 'bot.log',
#     maxBytes=1024* 1024* 10,
#     backupCount=5,
#     encoding='utf-8'
# )
logger.addHandler(fileHandler)
