from flask import render_template, request, redirect

from app import itinerary
from app.blueprints.itinerary.model import ItinerarySearch, ItineraryRequest
from app.blueprints.itinerary.service import search_itineraries, get_itinerary_detail, get_itinerary_request_by_id, \
    find_city_meta
from app.blueprints.template import template
from app.blueprints.traveler.model import CreateTravelerRequest, ConfirmTravelerSignupRequest
from app.blueprints.traveler.service import create_traveler, signup_request_exists, \
    handle_signup_confirmation


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

# organization
@template.get('/organization/dashboard')
def organization_dashboard():
    return render_template('organization-dashboard.html')

@template.get('/organization/signup')
def organization_signup():
    return render_template("organization-signup.html")

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

    if not interested_in:
        return render_template('itinerary-search.html')

    search = ItinerarySearch(interested_in=[interested_in])
    itineraries = search_itineraries(search)
    return render_template('itinerary-search.html', itineraries=itineraries)

