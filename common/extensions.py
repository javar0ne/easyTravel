import os

from flask_apscheduler import APScheduler
from flask_mailman import Mail
from openai import OpenAI
from pymongo import MongoClient
from redis import Redis

# general
APP_HOST = os.getenv("APP_HOST", "http://127.0.0.1:5000")

# mail
mail = Mail()

NAME_APPLICATION = "easyTravel"

# redis_auth
DAILY_EXPIRE = 60*60*24
redis_auth = Redis(host=os.getenv('REDIS_HOST', '127.0.0.1'), port=6379, password=os.getenv('REDIS_PASSWORD', 'admin'), db=0)
redis_city_description = Redis(host=os.getenv('REDIS_HOST', '127.0.0.1'), port=6379, password=os.getenv('REDIS_PASSWORD', 'admin'), db=1)

CITY_KEY_SUFFIX = "itinerary-description"

# mongodb
mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:admin@127.0.0.1:27017/')
mongo_client = MongoClient(mongo_uri)
db = mongo_client[NAME_APPLICATION]

# openai
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
assistant = OpenAI()

MAX_COMPLETION_TOKEN=16383

CITY_DESCRIPTION_USER_PROMPT = "Provide a short description of {city} city."
CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS = {
    "role": "system",
    "content": "Answer with a short description of the city provided with its latitude, longitude and name."
}

ITINERARY_USER_PROMPT = """
    In {month} I’m visiting {city} {travelling_with}. I’m staying there for {trip_duration} day(s) and 
    with a range budget per person between {min_budget} and {max_budget} EUR.  
    I’m interested into: {interested_in}. 
"""

ITINERARY_DAILY_PROMPT = "Generate the itinerary for day {day}."

ITINERARY_SYSTEM_INSTRUCTIONS = {
    "role": "system",
    "content": """
        Pretend to be a travel agency: you have to create an itinerary for the user based on his/her inputs.
        The user will provide you: the city he/she wants to visit, the trip duration (in days), a range of budget
        per day and for each person, the activities he/she would like to do, if the itineray should be accessible
        for handicapped people and if it is a solo, couple, family or friends trip.
        You have to prepare at least one activity per day.
        Your answer must be similar to the following json:
        
        {
            "itinerary": [
              {
                "day": 1,
                "title": "Classic Paris Sights",
                "stages": [
                  {
                    "period": "Morning",
                    "title": "Eiffel Tower",
                    "description": "Visit the iconic Eiffel Tower. The tower has elevators providing access to the 2nd floor and the summit for visitors with limited mobility.",
                    "cost": "€11.30-28.30 per person",
                    "distance_from_center": 4.2,
                    "accessible": true,
                    "coordinates": {
                      "lat": "48.8584",
                      "lng": "2.2945"
                    },
                    "avg_duration": 180
                  },
                  {
                    "period": "Lunch",
                    "title": "Rue Cler",
                    "description": "Enjoy a casual lunch at Rue Cler street market, which is flat and easy to navigate. Many cafes have outdoor seating and accessible entrances.",
                    "cost": "€15-20 for two",
                    "distance_from_center": 3.5,
                    "accessible": true,
                    "coordinates": {
                      "lat": "48.8561",
                      "lng": "2.3047"
                    },
                    "avg_duration": 90
                  },
                  {
                    "period": "Afternoon",
                    "title": "Seine River Cruise",
                    "description": "Take a Seine River Cruise. Many companies offer boats that are wheelchair-accessible, with ramps and adapted seating.",
                    "cost": "€15 per person",
                    "distance_from_center": 1.0,
                    "accessible": true,
                    "coordinates": {
                      "lat": "48.8566",
                      "lng": "2.3522"
                    },
                    "avg_duration": 60
                  },
                  {
                    "period": "Dinner",
                    "title": "Le Marais District",
                    "description": "Explore Le Marais and dine at a restaurant with wheelchair accessibility. Many bistros and falafel spots in this area have accessible entrances or nearby options.",
                    "cost": "€25-30 for two",
                    "distance_from_center": 1.5,
                    "accessible": true,
                    "coordinates": {
                      "lat": "48.8584",
                      "lng": "2.3616"
                    },
                    "avg_duration": 120
                  }
                ]
              }
            ]
        }
    """
}

#job
scheduler = APScheduler()
JOB_NOTIFICATION_DAILY_TRAVEL_TRIGGER = "cron"
JOB_NOTIFICATION_DAILY_TRAVEL_HOUR = 1
JOB_NOTIFICATION_DAILY_TRAVEL_MINUTES = 34