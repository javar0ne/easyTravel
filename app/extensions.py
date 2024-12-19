from flask_apscheduler import APScheduler
from flask_mailman import Mail

from app.assistant import Assistant
from app.wrappers import RedisWrapper, MongoWrapper, UnsplashWrapper

# mail
mail = Mail()

# redis
redis_auth = RedisWrapper(db=0)
redis_itinerary = RedisWrapper(db=2)
DAILY_EXPIRE = 60 * 60 * 24
MOST_SAVED_ITINERARIES_KEY = "most-saved-itineraries"

# mongodb
mongo = MongoWrapper()

# unsplash
unsplash = UnsplashWrapper()

# openai
assistant = Assistant()

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

ITINERARY_USER_EVENT_PROMPT = """
    In {month} I’m visiting {city} {travelling_with}. I’m staying there for {trip_duration} day(s) and 
    with a range budget per person between {min_budget} and {max_budget} EUR.  
    I’m interested into: {interested_in}. 

    Add the following activity to the itinerary:
    {{
        "period": "{event_period}",
        "title": "{event_title}",
        "description": "{event_description}",
        "cost": "{event_cost}",
        "accessible": {event_accessible},
        "coordinates": {{
          "lat": "{event_lat}",
          "lng": "{event_lng}"
        }},
        "avg_duration": {event_avg_duration}
    }}
"""

ITINERARY_DAILY_PROMPT = "Generate the itinerary for day {day}."

ITINERARY_RETRIEVE_DOCS_PROMPT = """
In {month} I'm going to {city}. what should I prepare for the trip? documents, visa, vaccinations
Format your answer in json like the following example:

{{
    "mandatory": [
        {{
            "name": "Passport",
            "description": "Must be valid for at least 6 months beyond the entry date into China and have at least two blank pages for stamps."
        }},
        {{
            "name": "Visa",
            "description": "Italian citizens need a tourist visa to enter China. The standard visa is a Type L, typically allowing stays of about 30 days, although duration may vary. Apply through the Chinese embassy, consulate, or an authorized agency, with passport, passport photo, completed application form, and travel itinerary (flight and hotel details)."
        }},
        {{
            "name": "Vaccinations",
            "description": "No mandatory vaccinations for Italian travelers, but certain ones are recommended."
        }}
    ],
    "recommended": [
        {{
            "name": "Recommended Vaccinations",
            "description": "Hepatitis A and B, typhoid (especially if traveling to less touristy areas or eating street food), and up-to-date routine vaccines (MMR, tetanus, diphtheria)."
        }},
        {{
            "name": "COVID-19 Requirements",
            "description": "Carry proof of COVID-19 vaccination or Green Pass if required. Verify any specific entry requirements for COVID-19 testing or proof of vaccination."
        }},
        {{
            "name": "Health Insurance",
            "description": "Medical insurance is highly recommended as medical costs in China can be high for foreigners. Ensure coverage includes medical emergencies, hospitalization, and medical repatriation."
        }},
        {{
            "name": "Language Preparation",
            "description": "Familiarize yourself with basic Chinese phrases or download a translation app, as English may not be widely understood."
        }},
        {{
            "name": "Payment Methods",
            "description": "China commonly uses electronic payment apps like WeChat Pay and Alipay, though these usually require a local bank account. Bring an international credit card and some cash for small purchases."
        }},
        {{
            "name": "Clothing",
            "description": "February in Shanghai is cold, with temperatures around or below 10Â°C. Pack winter clothing if planning to spend time outdoors."
        }}
    ]
}}
"""

ITINERARY_SYSTEM_INSTRUCTIONS = {
    "role": "system",
    "content": """
        Pretend to be a travel agency: you have to create an itinerary for the user based on his/her inputs.
        The user will provide you: the city he/she wants to visit, the trip duration (in days), a range of budget
        per day and for each person, the activities he/she would like to do, if the itinerary should be accessible
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

# job
scheduler = APScheduler()
JOB_NOTIFICATION_DAILY_TRAVEL_TRIGGER = "cron"
JOB_NOTIFICATION_DAILY_TRAVEL_HOUR = 1
JOB_NOTIFICATION_DAILY_TRAVEL_MINUTES = 34

JOB_NOTIFICATION_DOCS_REMINDER_TRIGGER = "cron"
JOB_NOTIFICATION_DOCS_REMINDER_HOUR = 1
JOB_NOTIFICATION_DOCS_REMINDER_MINUTES = 34
JOB_NOTIFICATION_DOCS_REMINDER_DAYS_BEFORE_START_DATE = 15

JOB_EVENT_NEWSLETTER_TRIGGER = "cron"
JOB_EVENT_NEWSLETTER_HOUR = 22
JOB_EVENT_NEWSLETTER_MINUTES = 38