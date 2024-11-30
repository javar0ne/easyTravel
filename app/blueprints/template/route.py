from dateutil.zoneinfo.rebuild import rebuild
from flask import render_template

from app.blueprints.template import template


# user
@template.get('/login')
def login():
    return render_template("login.html")
#admin
@template.get('/admin/dashboard')
def admin_dashboard():
    return render_template("admin-dashboard.html")

# traveler
@template.get('/traveler/signup')
def traveler_signup():
    return render_template("traveler-signup.html")

@template.get('/traveler/signup-confirmation')
def traveler_signup_confirmation():
    return render_template('traveler-signup-confirmation.html')

@template.get('/traveler/dashboard')
def traveler_dashboard():
    return render_template('traveler-dashboard.html')

# organization
@template.get('/organization/dashboard')
def organization_dashboard():
    return render_template('organization-dashboard.html')

