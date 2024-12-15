from flask import render_template, request, redirect

from app.blueprints.event.service import get_event_by_id
from app.blueprints.itinerary.model import ItinerarySearch
from app.blueprints.itinerary.service import search_itineraries, get_itinerary_detail, get_itinerary_request_by_id, \
    find_city_meta
from app.blueprints.organization.model import CreateOrganizationRequest
from app.blueprints.organization.service import create_organization
from app.blueprints.template import template
from app.blueprints.traveler.model import CreateTravelerRequest, ConfirmTravelerSignupRequest
from app.blueprints.traveler.service import create_traveler, signup_request_exists, \
    handle_signup_confirmation
from app.models import Coordinates


# user
@template.get('/login')
def login():
    return render_template("login.html")

@template.get('/forgot-password')
def forgot_password():
    return render_template("forgot-password.html")

#admin
@template.get('/admin/dashboard')
def admin_dashboard():
    return render_template("admin-dashboard.html")

# traveler
@template.route('/traveler/signup', methods=['GET', 'POST'])
def traveler_signup():
    if request.method == 'GET':
        return render_template("traveler-signup.html")

    traveler_request = CreateTravelerRequest(
        email=request.form.get('email'),
        password=request.form.get('password'),
        currency=request.form.get('currency'),
        first_name=request.form.get('first_name'),
        last_name=request.form.get('last_name'),
        birth_date=request.form.get('birth_date'),
        phone_number=request.form.get('phone_number')
    )

    create_traveler(traveler_request)

    return redirect('/login')

@template.get('/traveler/signup-confirmation/<token>')
def traveler_signup_confirmation(token):
    if signup_request_exists(token):
        return render_template('traveler-signup-confirmation.html', token=token)

    return redirect('/login')

@template.post('/traveler/signup-confirmation')
def traveler_signup_confirmation_post():
    signup_request = ConfirmTravelerSignupRequest(token=request.form.get('token'), interested_in=request.form.getlist('interested_in'))
    handle_signup_confirmation(signup_request)

    return redirect('/login')

@template.get('/traveler/dashboard')
def traveler_dashboard():
    return render_template('traveler-dashboard.html')

@template.get('/traveler/profile')
def traveler_profile():
    return render_template('traveler-profile.html')

# organization
@template.get('/organization/dashboard')
def organization_dashboard():
    return render_template('organization-dashboard.html')

@template.route('/organization/signup', methods=['GET', 'POST'])
def organization_signup():
    if request.method == "GET":
        return render_template("organization-signup.html")

    organization_request = CreateOrganizationRequest(
        email=request.form.get('email'),
        password=request.form.get('password'),
        organization_name=request.form.get('organization_name'),
        coordinates=Coordinates(lat=request.form.get('lat'), lng=request.form.get('lng')),
        website=request.form.get('website'),
        phone_number=request.form.get('phone_number')
    )
    create_organization(organization_request)

    return redirect('/login')

@template.get('/organization/profile')
def organization_profile():
    return render_template("organization-profile.html")

# event
@template.route('/event', defaults={'event_id': None})
@template.route('/event/<event_id>')
def event_detail(event_id):
    if not event_id:
        return render_template("detail-event.html", event=None)

    event = get_event_by_id(event_id)
    return render_template("detail-event.html", event=event)

# itinerary
@template.get("/itinerary/generate")
def generate_itinerary():
    return render_template("generate-itinerary.html")

@template.get("/itinerary/request/<itinerary_request_id>")
def itinerary_request(itinerary_request_id):
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    itinerary_request = get_itinerary_request_by_id(itinerary_request_id)
    city_meta = find_city_meta(itinerary_request.city)
    return render_template("itinerary-request.html", itinerary_request=itinerary_request, city_meta=city_meta, lat=lat, lng=lng)

@template.get("/itinerary/detail/<itinerary_id>")
def itinerary_detail(itinerary_id):
    itinerary = get_itinerary_detail(itinerary_id)
    return render_template("itinerary-detail.html", itinerary=itinerary)

@template.get('/itinerary/search')
def itinerary_search():
    interested_in = request.args.get('interested_in')
    city = request.args.get('city')
    people = request.args.get('people')
    budget = request.args.get('budget')

    if not interested_in and not city and not people and not budget:
        return render_template('search-itinerary.html', itineraries=[])

    search = ItinerarySearch.from_request(interested_in, city, people, budget)
    itineraries = search_itineraries(search)

    return render_template(
        'search-itinerary.html',
        itineraries=itineraries,
        searched_city=city,
        searched_activity=interested_in,
        searched_people=people,
        searched_budget=budget
    )

@template.get('/itinerary/upcoming')
def itinerary_upcoming():
    return render_template('itinerary-upcoming.html')
