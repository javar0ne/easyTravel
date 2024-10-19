import os

from pymongo import MongoClient
from redis import Redis
from openai import OpenAI

# redis
DAILY_EXPIRE = 60*60*24
redis = Redis(host=os.getenv('REDIS_HOST', '127.0.0.1'), port=6379, password=os.getenv('REDIS_PASSWORD', 'admin'))

# mongodb
mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:admin@mongodb:27017/')
mongo_client = MongoClient(mongo_uri)
db = mongo_client['easyTravel']

# openai
assistant = OpenAI()