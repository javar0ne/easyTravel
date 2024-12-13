import logging

from flask import request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from openai import APIStatusError
from pydantic import ValidationError

from app.blueprints.itinerary import itinerary
from app.blueprints.itinerary.model import ItineraryRequest, ShareWithRequest, PublishReqeust, DuplicateRequest, \
    ItinerarySearch, DateNotValidException, UpdateItineraryRequest, CannotUpdateItineraryException, \
    ItineraryGenerationDisabledException, CityMetaRequest
from app.blueprints.itinerary.service import get_city_description, get_itinerary_request_by_id, \
    get_itinerary_by_id, create_itinerary, share_with, publish, completed, duplicate, update_itinerary, \
    search_itineraries, get_completed_itineraries, get_shared_itineraries, download_itinerary, delete_itinerary, \
    get_saved_itineraries, handle_itinerary_request, handle_event_itinerary_request, handle_save_itinerary, \
    get_most_saved, get_itinerary_meta_detail, find_city_meta
from app.exceptions import ElementNotFoundException
from app.models import Paginated
from app.response_wrapper import success_response, bad_gateway_response, error_response, bad_request_response, \
    no_content_response, not_found_response, service_unavailable_response
from app.role import roles_required, Role

logger = logging.getLogger(__name__)

@itinerary.get('/<itinerary_id>')
def get_itinerary(itinerary_id):
    try:
        itinerary = get_itinerary_by_id(itinerary_id)
        return success_response(itinerary.model_dump())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/create/<itinerary_request_id>')
@roles_required([Role.TRAVELER.name])
def create(itinerary_request_id):
    try:
        inserted_id = create_itinerary(itinerary_request_id)
        return success_response({"id": inserted_id})
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.put('/<itinerary_id>')
def update(itinerary_id):
    try:
        updated_itinerary = UpdateItineraryRequest(**request.json)
        update_itinerary(itinerary_id, updated_itinerary)

        return no_content_response()
    except ValidationError as err:
        logger.error("validation error while parsing itinerary request", err)
        return bad_request_response(err.errors())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except CannotUpdateItineraryException as err:
        logger.warning(err.message)
        return bad_request_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.delete('/<itinerary_id>')
def delete(itinerary_id):
    try:
        delete_itinerary(itinerary_id)

        return no_content_response()
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()


@itinerary.get("/download/<itinerary_id>")
def download(itinerary_id):
    try:
        pdf_file = download_itinerary(itinerary_id)
        return send_file(pdf_file,
                         as_attachment=True,
                         download_name="itinerary.pdf",
                         mimetype="application/pdf")
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/search')
def search():
    try:
        itinerary_search = ItinerarySearch(**request.json)
        itineraries = search_itineraries(itinerary_search)

        return success_response(itineraries.model_dump())
    except ValidationError as err:
        logger.error("validation error while parsing share itinerary with request", err)
        return bad_request_response(err.errors(include_context=False))
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.get('/completed')
@roles_required([Role.TRAVELER.name])
def completed_itineraries():
    try:
        itineraries = get_completed_itineraries(get_jwt_identity())
        return success_response(itineraries)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/save/<itinerary_id>')
@roles_required([Role.TRAVELER.name])
def save_itinerary(itinerary_id):
    try:
        handle_save_itinerary(get_jwt_identity(), itinerary_id)
        return no_content_response()
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.get('/saved')
@roles_required([Role.TRAVELER.name])
def saved_itineraries():
    try:
        paginated = Paginated(**request.json)
        itineraries = get_saved_itineraries(get_jwt_identity(), paginated)
        return success_response(itineraries.model_dump())
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/shared')
@roles_required([Role.TRAVELER.name])
def shared_itineraries():
    try:
        paginated = Paginated(**request.json)
        itineraries = get_shared_itineraries(get_jwt_identity(), paginated)

        return success_response(itineraries.model_dump())
    except ValidationError as err:
        logger.error("validation error while parsing shared itineraries reqeust", err)
        return bad_request_response(err.errors(include_context=False))
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/share-with')
def share_itinerary_with():
    try:
        users = ShareWithRequest(**request.json)
        share_with(users)

        return no_content_response()
    except ValidationError as err:
        logger.error("validation error while parsing share itinerary with reqeust", err)
        return bad_request_response(err.errors(include_context=False))
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/publish')
def publish_itinerary():
    try:
        publish(PublishReqeust(**request.json))

        return no_content_response()
    except ValidationError as err:
        logger.error("validation error while parsing publish itinerary reqeust", err)
        return bad_request_response(err.errors(include_context=False))
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/completed/<itinerary_id>')
def itinerary_completed(itinerary_id):
    try:
        completed(itinerary_id)

        return no_content_response()
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/duplicate')
@jwt_required()
def duplicate_itinerary():
    try:
        inserted_id = duplicate(get_jwt_identity(), DuplicateRequest(**request.json))

        return success_response({"id": inserted_id})
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/city-meta')
def city_description():
    try:
        city_meta_req = CityMetaRequest(**request.json)
        meta = find_city_meta(city_meta_req.name)

        if not meta:
            return no_content_response()

        return success_response(meta.model_dump())
    except APIStatusError as err:
        logger.error(str(err))
        return bad_gateway_response()
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/request')
@roles_required([Role.TRAVELER.name])
def generate_itinerary():
    try:
        logger.debug("parsing request body..")
        itinerary_request = ItineraryRequest(**request.json)
        request_id = handle_itinerary_request(get_jwt_identity(), itinerary_request)
        return success_response({"request_id": str(request_id)})
    except ValidationError as err:
        logger.error("validation error while parsing itinerary request", err)
        return bad_request_response(err.errors(include_context=False))
    except DateNotValidException as err:
        logger.error(str(err))
        return bad_request_response(err.message)
    except ItineraryGenerationDisabledException as err:
        logger.error(err.message)
        return service_unavailable_response()
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/event-itinerary-request/<event_id>')
@roles_required([Role.TRAVELER.name])
def generate_event_itinerary(event_id):
    try:
        logger.debug("parsing request body..")
        itinerary_request = ItineraryRequest(**request.json)
        request_id = handle_event_itinerary_request(get_jwt_identity(), itinerary_request, event_id)
        return success_response({"request_id": str(request_id)})
    except ValidationError as err:
        logger.error("validation error while parsing itinerary request", err)
        return bad_request_response(err.errors(include_context=False))
    except DateNotValidException as err:
        logger.error(str(err))
        return bad_request_response(err.message)
    except ItineraryGenerationDisabledException as err:
        logger.error(err.message)

    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.get('/request/<request_id>')
def get_itinerary_request(request_id):
    try:
        itinerary_request = get_itinerary_request_by_id(request_id)
        return success_response(itinerary_request.model_dump())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.get('/most-saved')
def most_saved():
    try:
        spotlight_itineraries = get_most_saved()
        return success_response(spotlight_itineraries)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.get('/meta/detail/<itinerary_id>')
@roles_required([Role.TRAVELER.name])
def itinerary_meta_detail(itinerary_id):
    try:
        meta_detail = get_itinerary_meta_detail(get_jwt_identity(), itinerary_id)
        return success_response(meta_detail.model_dump())
    except Exception as err:
        logger.error(str(err))
        return error_response()
