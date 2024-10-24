import logging

logger = logging.getLogger(__name__)
#logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)
format = '%(asctime)s%(levelname)s:%(message)s'
#for more: https://docs.python.org/3/howto/logging.html
logging.basicConfig(format=format, encoding='utf-8', level=logging.DEBUG)

def debug(msg):
	logging.debug(msg)

def info(msg):
	logging.info(msg)

def warning(msg):
	logging.warning(msg)

def error(msg):
	logging.error(msg)