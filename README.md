# **easyTravel**  
*Your AI-powered travel itinerary planner.*

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue?style=flat-square)](LICENSE)

![Traveler Dashboard](assets/traveler-dashboard.png)

![Itinerary Detail](assets/itinerary-detail.png)

---

## **Table of Contents**  
- [About the Project](#about-the-project)  
- [Key Features](#key-features)  
- [Getting Started](#getting-started)  
- [Usage](#usage)  
- [License](#license)  

---

## **About the Project**  
**easyTravel** is an innovative platform that helps travelers design personalized travel itineraries tailored to their preferences. 
Leveraging an AI agent, users can effortlessly plan trips: whether you're a solo traveler or planning a group trip, easyTravel simplifies your travel planning journey.

If you're an organization and want to sponsor your upcoming events, with easyTravel you can create and notify them to travelers which interests match with the event.

---

## **Key Features**  
### **Travelers**
- **Easy itinerary planning**: Generate your itinerary based on your preferences thanks to an AI agent.
- **Never alone**: Stay updated with your daily schedule, weather, travel advisories, and events at your destinations.
- **Inspire the community**: Share your itineraries with the community and let all travelers be inspired by your journeys.
- **Invite your friends**: Invite your friends and let them know about your upcoming trips.

### **Organizations**
- **Events**: Create upcoming events (exhibits, festivals, concerts and so on)
- **Sponsor your events**: Let travelers know about your events and make them create itineraries to join you.

---

## **Getting Started**
### **Prerequisites**  
- Docker  
- A modern web browser
### **Installation**  
1. Clone the repository:  
   ```bash
   git clone https://github.com/javar0ne/easyTravel.git
   cd easyTravel
   ```  

2. Set up the environment variables:  
   - Create a `.env` file in the `docker` directory.  
   - Add API keys and necessary configuration:
     ```env
     # flask
     JWT_SECRET_KEY=your_jwt_secret_key
     MAIL_USERNAME=your_mail_username
     MAIL_PASSWORD=your_mail_password
     REDIS_PASSWORD=redis_password
     ADMIN_MAIL=your_admin_mail
     ADMIN_PASSWORD=your_admin_password
     OPENAI_API_KEY=your_openai_api_key
     UNSPLASH_BASE_URL=unsplash_base_url
     UNSPLASH_ACCESS_KEY=your_unsplash_access_key
        
     # mongodb
     MONGO_INITDB_ROOT_USERNAME=your_mongo_root_username
     MONGO_INITDB_ROOT_PASSWORD=your_mongo_root_password
        
     # redis
     REDIS_PASSWORD=your_redis_password
        
     # redis-commander
     REDIS_COMMANDER_USER=your_redis_commander_user
     REDIS_COMMANDER_PASSWORD=your_redis_commander_password
     ```
   - Some configs are provided by default, but you might need to change them:
     ```env
     LOG_LEVEL=DEBUG
     JWT_ACCESS_TOKEN_EXPIRES=15
     
     MAIL_SERVER=smtp.gmail.com
     MAIL_PORT=587
     MAIL_DEFAULT_SENDER=no-reply@easytravel.com
     
     REDIS_HOST=127.0.0.1
     REDIS_PASSWORD=6379
     
     MONGO_URI=mongodb://admin:admin@127.0.0.1:27017/
     MONGO_DATABASE=easyTravel
     
     OPENAI_MODEL=gpt-4o-mini
     ```

3. Start the development server:  
   ```bash
   cd docker
   docker compose up -d
   ```  

4. Open the application in your browser:  
   ```
   http://localhost
   ```

---

## **Usage**  
### **Traveler**
1. **Sign Up** or **Log In**.
2. **Create** your itinerary.
3. **Share** your itinerary.
4. **Duplicate** community itineraries.
5. **Invite** your travel companions to your trip.
### **Organization**
1. **Sign Up** or **Log In** to your account.   
2. **Create** your events.
3. **Sponsor** them thanks to newsletter.

---

## **License**  
Distributed under the Apache 2.0 License. See `LICENSE` for more information.

---

## **Acknowledgments**  
- [OpenAI](https://openai.com) for the AI agent.  
- [Leaflet](https://leafletjs.com/) for interactive maps.
- [Unsplash](https://unsplash.com/) for images.
- [REST Countries](https://restcountries.com/) for countries capital search.