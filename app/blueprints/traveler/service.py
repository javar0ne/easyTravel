import logging
import secrets
from datetime import datetime, timezone

from bson import ObjectId
from flask import url_for

from app.blueprints.traveler.mail import send_traveler_signup_mail
from app.blueprints.traveler.model import CreateTravelerRequest, UpdateTravelerRequest, Traveler, \
    ConfirmTravelerSignupRequest, TravelerSignupConfirmationNotFoundException, TravelerFull
from app.blueprints.user.service import create_user, get_user_by_id, update_user_email
from app.exceptions import ElementNotFoundException
from app.extensions import mongo
from app.models import Collections
from app.role import Role

logger = logging.getLogger(__name__)

def exists_by_id(traveler_id: str) -> bool:
    return mongo.count_documents(Collections.TRAVELERS, {"_id": ObjectId(traveler_id)}) > 0

def get_traveler_by_id(traveler_id: str) -> Traveler:
    logger.info("retrieving traveler with id %s", traveler_id)
    traveler_document = mongo.find_one(Collections.TRAVELERS, {'_id': ObjectId(traveler_id)})

    if traveler_document is None:
        raise ElementNotFoundException(f"no traveler found with id: {traveler_id}")

    logger.info("found traveler with id %s", traveler_id)
    return Traveler(**traveler_document)

def get_full_traveler_by_id(user_id: str) -> Traveler:
    logger.info("retrieving traveler with user id %s", user_id)
    user = get_user_by_id(user_id)
    traveler_document = mongo.find_one(Collections.TRAVELERS, {'user_id': user.id})

    if traveler_document is None:
        raise ElementNotFoundException(f"no traveler found with id: {user.id}")

    traveler = Traveler(**traveler_document)

    logger.info("found traveler with id %s", user.id)
    return TravelerFull.from_sources(traveler, user)

def get_traveler_by_user_id(user_id: str) -> Traveler:
    logger.info("retrieving traveler with user id %s", user_id)
    traveler_document = mongo.find_one(Collections.TRAVELERS, {'user_id': user_id, "deleted_at": None})

    if traveler_document is None:
        raise ElementNotFoundException(f"no traveler found with user id: {user_id}")

    logger.info("found traveler with user id %s", user_id)
    return Traveler(**traveler_document)

def save_traveler_signup(traveler_id: str, email: str):
    logger.info("saving traveler signup for traveler with id %s", traveler_id)
    token = secrets.token_urlsafe(16)
    mongo.insert_one(
        Collections.TRAVELER_SIGNUPS,
        {
            "traveler_id": traveler_id,
            "token": token
        }
    )
    url_signup_confirmation = url_for("template.traveler_signup_confirmation", token=token, _external=True)
    logger.info(url_signup_confirmation)
    send_traveler_signup_mail(url_signup_confirmation, email)
    logger.info("saved traveler signup for traveler with id %s", traveler_id)

def create_traveler(request: CreateTravelerRequest) -> str:
    logger.info("storing traveler..")
    user_id = create_user(request.email, request.password, [Role.TRAVELER.name])

    request.user_id = str(user_id)
    traveler = Traveler.from_create_req(request)
    traveler.created_at = datetime.now(timezone.utc)
    stored_traveler = mongo.insert_one(Collections.TRAVELERS, traveler.model_dump(exclude={"id"}))

    save_traveler_signup(str(stored_traveler.inserted_id), request.email)

    logger.info("traveler stored successfully with id %s", stored_traveler.inserted_id)

    return str(stored_traveler.inserted_id)

def update_traveler(user_id: str, updated_traveler: UpdateTravelerRequest):
    logger.info("updating traveler with id %s..", user_id)
    stored_traveler = get_traveler_by_user_id(user_id)
    if not stored_traveler:
        raise ElementNotFoundException(f"no traveler found with id: {user_id}")

    if updated_traveler.email:
        update_user_email(user_id, updated_traveler.email)

    stored_traveler.update_by(updated_traveler)
    stored_traveler.updated_at = datetime.now(timezone.utc)
    mongo.update_one(
        Collections.TRAVELERS,
        {'user_id': user_id},
        {'$set': stored_traveler.model_dump(exclude={"id"})}
    )
    logger.info("traveler with id %s updated successfully", user_id)

def handle_signup_confirmation(request: ConfirmTravelerSignupRequest):
    logger.info("confirming traveler signup..")
    traveler_signup = get_signup_request(request.token)

    mongo.update_one(
        Collections.TRAVELERS,
        {"_id": ObjectId(traveler_signup.get("traveler_id"))},
        {"$set": {"interested_in": request.interested_in, "updated_at": datetime.now(timezone.utc)}}
    )

    mongo.delete_one(Collections.TRAVELER_SIGNUPS, {"token": request.token})
    logger.info("traveler signup confirmed for traveler with id %s!", traveler_signup.get("traveler_id"))


def signup_request_exists(token: str):
    return mongo.exists(Collections.TRAVELER_SIGNUPS, {'token': token})

def get_signup_request(token: str):
    traveler_signup = mongo.find_one(Collections.TRAVELER_SIGNUPS, {'token': token})

    if not traveler_signup:
        raise TravelerSignupConfirmationNotFoundException()

    return traveler_signup
