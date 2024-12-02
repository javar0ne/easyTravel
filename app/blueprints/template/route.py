import logging

from flask import render_template, request, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.blueprints.template import template
from app.blueprints.traveler.model import CreateTravelerRequest, ConfirmTravelerSignupRequest
from app.blueprints.traveler.service import create_traveler, signup_request_exists, \
    handle_signup_confirmation, get_traveler_by_user_id

logger = logging.getLogger(__name__)

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
@jwt_required()
def traveler_dashboard():
    traveler = get_traveler_by_user_id(get_jwt_identity())
    return render_template('traveler-dashboard.html', traveler=traveler)

# organization
@template.get('/organization/dashboard')
def organization_dashboard():
    return render_template('organization-dashboard.html')

@template.get('/organization/signup')
def organization_signup():
    return render_template("organization-signup.html")

@template.get("/generate-itinerary")
def generate_itinerary():
    return render_template("generate-itinerary.html")