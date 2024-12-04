import requests
from flask import Flask
from pymongo import MongoClient
from redis import Redis

from app.models import Collections, UnsplashSingleResponse


class UnsplashWrapper:
    def __init__(self):
        self.base_url = None
        self.access_key = None

    def init_app(self, app: Flask):
        self.base_url = app.config["UNSPLASH_BASE_URL"]
        self.access_key = app.config["UNSPLASH_ACCESS_KEY"]

    def build_headers(self):
        return { "Authorization": f"Client-ID {self.access_key}" }

    def find_one(self, city: str) -> UnsplashSingleResponse:
        url = f"{self.base_url}/search/photos?query={city}&orientation=landscape&page=1&per_page=1"
        response = requests.get(url, headers=self.build_headers(), verify=False)

        if response.status_code == 200:
            return UnsplashSingleResponse(**response.json().get("results")[0])

class RedisWrapper:
    def __init__(self, db: int = 0):
        self.client = None
        self.db = db

    def init_app(self, app: Flask):
        self.client = Redis(
            host=app.config['REDIS_HOST'],
            port=app.config['REDIS_PORT'],
            password=app.config['REDIS_PASSWORD'],
            db=self.db
        )

    def get_client(self) -> Redis:
        if not self.client:
            raise RuntimeError("no instance provided for redis client")

        return self.client

class MongoWrapper:
    def __init__(self):
        self.client = None
        self.db = None

    def init_app(self, app: Flask):
        self.client = MongoClient(app.config["MONGO_URI"])
        self.db = app.config["MONGO_DATABASE"]

    def get_client(self) -> MongoClient:
        if not self.client:
            raise RuntimeError("no instance provided for mongo client")

        return self.client

    def get_collection(self, collection):
        return self.get_client()[self.db][self.decode_collection(collection)]

    def count_documents(self, collection, filters: dict):
        self.add_base_filters(filters)
        return self.get_collection(collection).count_documents(filters)

    def find_one(self, collection, filters: dict, projection: dict = None):
        self.add_base_filters(filters)

        if not projection:
            return self.get_collection(collection).find_one(filters)

        return self.get_collection(collection).find_one(filters, projection)

    def exists(self, collection, filters: dict):
        self.add_base_filters(filters)
        return self.get_collection(collection).count_documents(filters) > 0

    def exists_one(self, collection, filters: dict):
        self.add_base_filters(filters)
        return self.get_collection(collection).count_documents(filters) == 1

    def insert_one(self, collection, obj: dict):
        return self.get_collection(collection).insert_one(obj)

    def update_one(self, collection, filters: dict, update: dict):
        self.add_base_filters(filters)
        return self.get_collection(collection).update_one(filters, update)

    def delete_one(self, collection, filters: dict):
        return self.get_collection(collection).delete_one(filters)

    def find(self, collection, filters: dict, projection: dict = None):
        self.add_base_filters(filters)

        if projection is None:
            return self.get_collection(collection).find(filters)

        return self.get_collection(collection).find(filters, projection)

    def aggregate(self, collection, filters: dict, aggregations: list[dict]):
        return self.get_collection(collection).aggregate([self.build_match(filters)] + aggregations)

    def build_match(self, filters: dict):
        self.add_base_filters(filters)
        return {"$match": filters}

    def add_base_filters(self, filters: dict):
        filters["deleted_at"] = None

    def decode_collection(self, collection):
        if isinstance(collection, Collections):
            return collection.value
        elif isinstance(collection, str):
            return collection

        raise RuntimeError("unknown collection type")
