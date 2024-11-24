from flask import render_template

from app.blueprints.template import template


@template.get('/login')
def login():
    return render_template("login.html")

# traveler
@template.get('/traveler/signup')
def traveler_signup():
    render_template("traveler-signup.html")

@template.get('/traveler/signup-confirmation')
def traveler_signup_confirmation():
    return render_template('traveler-signup-confirmation.html')