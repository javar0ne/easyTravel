import os

from pymongo import MongoClient
from redis import Redis

redis = Redis(host=os.getenv('REDIS_HOST', '127.0.0.1'), port=6379, password=os.getenv('REDIS_PASSWORD', 'admin'))

mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:admin@mongodb:27017/')
client = MongoClient(mongo_uri)
db = client['easyTravel']