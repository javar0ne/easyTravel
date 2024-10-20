import os

from pymongo import MongoClient
from redis import Redis
from openai import OpenAI

# redis_auth
DAILY_EXPIRE = 60*60*24
redis_auth = Redis(host=os.getenv('REDIS_HOST', '127.0.0.1'), port=6379, password=os.getenv('REDIS_PASSWORD', 'admin'), db=0)
redis_city_description = Redis(host=os.getenv('REDIS_HOST', '127.0.0.1'), port=6379, password=os.getenv('REDIS_PASSWORD', 'admin'), db=1)

# mongodb
mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:admin@mongodb:27017/')
mongo_client = MongoClient(mongo_uri)
db = mongo_client['easyTravel']

# openai
assistant = OpenAI()