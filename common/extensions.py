import os

from pymongo import MongoClient
from redis import Redis
from openai import OpenAI

# redis_auth
DAILY_EXPIRE = 60*60*24
redis_auth = Redis(host=os.getenv('REDIS_HOST', '127.0.0.1'), port=6379, password=os.getenv('REDIS_PASSWORD', 'admin'), db=0)
redis_city_description = Redis(host=os.getenv('REDIS_HOST', '127.0.0.1'), port=6379, password=os.getenv('REDIS_PASSWORD', 'admin'), db=1)

CITY_KEY_SUFFIX = "itinerary-description"

# mongodb
mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:admin@mongodb:27017/')
mongo_client = MongoClient(mongo_uri)
db = mongo_client['easyTravel']

# openai
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
assistant = OpenAI()
MAX_COMPLETION_TOKEN=16383
CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS = [
    {
        "role": "system",
        "content": "Answer with a short description of the city provided with its latitude, longitude and name."
    }
]

ITINERARY_SYSTEM_INSTRUCTIONS = [
    {
        "role": "system",
        "content": """
            act as a travel agency, you must must create an itinerary for the user based on its inputs.
            user will provide you the city it wants to visit, trip duration (in days), a range of budget per person per day, if it is a solo, couple, family or friends trip, which activities it would like to do and if the itinerary must be accessible for handicapped people.
            for each day of the trip you must provide at least one activity.
            your answer must be similar to the following json:
            
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
                  },
                  {
                    "day": 2,
                    "title": "Montmartre & Art Exploration",
                    "stages": [
                      {
                        "period": "Morning",
                        "title": "Montmartre & Sacré-Cœur",
                        "description": "Although Montmartre is known for its hills, the area around Sacré-Cœur has accessible routes and a funicular to assist with mobility. The basilica is also wheelchair accessible.",
                        "cost": "Free",
                        "distance_from_center": 3.6,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8867",
                          "lng": "2.3431"
                        },
                        "avg_duration": 180
                      },
                      {
                        "period": "Lunch",
                        "title": "Café in Montmartre",
                        "description": "Have lunch at a Montmartre café. Many cafes have outdoor seating or wheelchair-accessible entrances.",
                        "cost": "€20-25 for two",
                        "distance_from_center": 3.6,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8860",
                          "lng": "2.3397"
                        },
                        "avg_duration": 90
                      },
                      {
                        "period": "Afternoon",
                        "title": "Musée d’Orsay",
                        "description": "Visit Musée d’Orsay, which is fully accessible for disabled visitors, with ramps, elevators, and adapted restrooms.",
                        "cost": "€16 per person",
                        "distance_from_center": 2.0,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8599",
                          "lng": "2.3266"
                        },
                        "avg_duration": 180
                      },
                      {
                        "period": "Dinner",
                        "title": "French Bistro in Montmartre",
                        "description": "Enjoy a cozy dinner or wine and cheese tasting at an accessible Montmartre bistro. Ensure to choose one with a flat entrance.",
                        "cost": "€30-35 for two",
                        "distance_from_center": 3.6,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8857",
                          "lng": "2.3393"
                        },
                        "avg_duration": 120
                      }
                    ]
                  },
                  {
                    "day": 3,
                    "title": "Adventure & Outdoor Fun",
                    "stages": [
                      {
                        "period": "Morning",
                        "title": "Hot Air Balloon Ride at Parc André Citroën",
                        "description": "Take a hot air balloon ride at Parc André Citroën. The park is accessible, and the balloon is equipped for people with limited mobility.",
                        "cost": "€15 per person",
                        "distance_from_center": 6.5,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8359",
                          "lng": "2.2700"
                        },
                        "avg_duration": 60
                      },
                      {
                        "period": "Lunch",
                        "title": "Rue Montorgueil",
                        "description": "Explore Rue Montorgueil and enjoy a picnic lunch. The area is flat and easy to navigate, with accessible food vendors and cafes.",
                        "cost": "€15-20 for two",
                        "distance_from_center": 1.5,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8674",
                          "lng": "2.3488"
                        },
                        "avg_duration": 90
                      },
                      {
                        "period": "Afternoon",
                        "title": "Latin Quarter Exploration",
                        "description": "Visit the Latin Quarter, which has many flat areas and is mostly accessible. Visit bookstores and cafes that are adapted for wheelchair access.",
                        "cost": "Free",
                        "distance_from_center": 1.0,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8493",
                          "lng": "2.3470"
                        },
                        "avg_duration": 120
                      },
                      {
                        "period": "Dinner",
                        "title": "Dinner in the Latin Quarter",
                        "description": "Dine at a wheelchair-accessible restaurant or fondue spot in the Latin Quarter. Most modern restaurants have accessibility.",
                        "cost": "€30-35 for two",
                        "distance_from_center": 1.0,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8500",
                          "lng": "2.3472"
                        },
                        "avg_duration": 120
                      }
                    ]
                  },
                  {
                    "day": 4,
                    "title": "Versailles Day Trip",
                    "stages": [
                      {
                        "period": "Morning",
                        "title": "Palace of Versailles",
                        "description": "Take an RER train to Versailles. The Palace of Versailles offers accessible entrances, and the gardens have paved paths. The palace also provides wheelchairs for those who need them.",
                        "cost": "€19.50 per person + €7 round trip (RER)",
                        "distance_from_center": 21.0,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8049",
                          "lng": "2.1204"
                        },
                        "avg_duration": 240
                      },
                      {
                        "period": "Lunch",
                        "title": "Picnic in Versailles",
                        "description": "Enjoy a picnic lunch in the accessible parts of the Versailles gardens, which have paved and flat areas suitable for wheelchairs.",
                        "cost": "€20 for two",
                        "distance_from_center": 21.0,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8049",
                          "lng": "2.1204"
                        },
                        "avg_duration": 90
                      },
                      {
                        "period": "Afternoon",
                        "title": "Explore Versailles Gardens",
                        "description": "Continue exploring the Versailles gardens on the accessible paths. Boats and bikes are available, but ensure they have accessibility accommodations before booking.",
                        "cost": "Free or small rental fee for boats/bikes",
                        "distance_from_center": 21.0,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8049",
                          "lng": "2.1204"
                        },
                        "avg_duration": 120
                      },
                      {
                        "period": "Dinner",
                        "title": "Return to Paris for Dinner",
                        "description": "Return to Paris and enjoy dinner at an accessible neighborhood brasserie with wheelchair-friendly entrances.",
                        "cost": "€30 for two",
                        "distance_from_center": 0.0,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8566",
                          "lng": "2.3522"
                        },
                        "avg_duration": 120
                      }
                    ]
                  },
                  {
                    "day": 5,
                    "title": "Louvre and Le Marais Exploration",
                    "stages": [
                      {
                        "period": "Morning",
                        "title": "Louvre Museum",
                        "description": "Visit the Louvre Museum, which is fully accessible for wheelchair users, with ramps, elevators, and adapted restrooms.",
                        "cost": "€17 per person",
                        "distance_from_center": 1.2,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8606",
                          "lng": "2.3376"
                        },
                        "avg_duration": 240
                      },
                      {
                        "period": "Lunch",
                        "title": "Takeaway near the Louvre",
                        "description": "Grab accessible takeaway food near the Louvre from vendors or cafes with flat entrances.",
                        "cost": "€15-20 for two",
                        "distance_from_center": 1.2,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8610",
                          "lng": "2.3368"
                        },
                        "avg_duration": 60
                      },
                      {
                        "period": "Afternoon",
                        "title": "Le Marais Walking Tour",
                        "description": "Explore the flat and wheelchair-accessible streets of Le Marais. Visit Place des Vosges and accessible shops.",
                        "cost": "Free",
                        "distance_from_center": 1.5,
                        "accessible": true,
                        "coordinates": {
                          "lat": "48.8584",
                          "lng": "2.3616"
                        },
                        "avg_duration": 180
                      },
                      {
                        "period": "Dinner",
                        "title": "French Gourmet Fare",
                        "description": "End your trip with dinner at a wheelchair-accessible French bistro offering a prix-fixe menu in Le Marais.",
                        "cost": "€40-50 for two",
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
]