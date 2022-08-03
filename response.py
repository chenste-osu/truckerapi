from flask import make_response
import json
from json2html import *

def response_OK(query_json, status_code):
    res_json = json.dumps(query_json, indent=4)
    response = make_response(res_json, status_code)
    return response

def response_OK_created(query_json, status_code):
    res_json = json.dumps(query_json, indent=4)
    response = make_response(res_json, status_code)
    response.mimetype = 'application/json'
    response.headers.set("Content-Location", query_json["self"])
    return response

def response_OK_json(query_json, status_code):
    res_json = json.dumps(query_json, indent=4)
    response = make_response(res_json, status_code)
    response.mimetype = 'application/json'
    response.headers.set("Content-Type", "application/json")
    return response

def response_OK_html(query_json, status_code):
    res_json = json.dumps(query_json, indent=4)
    response = make_response(json2html.convert(json = res_json))
    response.status_code = status_code
    response.mimetype = 'text/html'
    response.headers.set("Content-Type", "text/html")
    return response

def response_303(query_json):
    res_json = json.dumps(query_json, indent=4)
    response = make_response(res_json, 303)
    response.headers.set("Location", query_json["self"])
    response.mimetype = 'application/json'
    return response
    
def response_400_missing_truckdata():
    res_json = json.dumps({
        "Error": 
        ("The request object is missing at least one of the required attributes"
        ". Request must have name, length, type, and public attributes"
        )
    }, indent=4)

    response = make_response(res_json, 400)
    return response

def response_400_invalid_truckdata():
    res_json = json.dumps({
        "Error": 
        ("The request object has at least one invalid attribute. "
        "Only alphanumeric characters are supported for name and type. "
        "Only digits are supported for length. "
        "Only booleans are supported for public. "
        )
    }, indent=4)

    response = make_response(res_json, 400)
    return response

def response_400_missing_loaddata():
    res_json = json.dumps({
        "Error": 
        ("The request object is missing at least one of the required attributes"
        ". Request must have volume, item, and quantity attributes"
        )
    }, indent=4)

    response = make_response(res_json, 400)
    return response

def response_400_invalid_loaddata():
    res_json = json.dumps({
        "Error": 
        ("The request object has at least one invalid attribute. "
        "Only alphanumeric characters are supported for item. "
        "Only digits are supported for volume and quantity."
        )
    }, indent=4)

    response = make_response(res_json, 400)
    return response

def response_400_old_data():
    res_json = json.dumps({
        "Error": 
        ("PUT requests must have all required attributes and must be different"
        " from the original values."
        )
    }, indent=4)

    response = make_response(res_json, 400)
    return response

def response_401_mismatch():
    res_json = json.dumps({
        "Error": 
        ("Provided JWT does not match owner ID in URL"
        )
    }, indent=4)

    response = make_response(res_json, 401)
    return response

def response_403_truckname():
    res_json = json.dumps({
        "Error": 
        "The request contains a truck name that already exists"
    }, indent=4)

    response = make_response(res_json, 403)
    return response

def response_403_truck():
    res_json = json.dumps({
        "Error": 
        "JWT is valid, but the truck is owned by someone else"
    }, indent=4)

    response = make_response(res_json, 403)
    return response

def response_403_load():
    res_json = json.dumps({
        "Error": 
        "This load has already been assigned. You must first remove the current load from the carrier"
    }, indent=4)

    response = make_response(res_json, 403)
    return response

def response_404_truck():
    res_json = json.dumps({
        "Error": 
        "No truck with this truck_id exists"
    }, indent=4)

    response = make_response(res_json, 404)
    return response

def response_404_owner():
    res_json = json.dumps({
        "Error": 
        "No owner with this owner ID exists"
    }, indent=4)

    response = make_response(res_json, 404)
    return response

def response_404_load():
    res_json = json.dumps({
        "Error": 
        "No load with this load ID exists"
    }, indent=4)

    response = make_response(res_json, 404)
    return response

def response_404_both():
    res_json = json.dumps({
        "Error": 
        ("Either no truck with this truck ID exists"
        "or no load with this load ID exists"
        )
    }, indent=4)

    response = make_response(res_json, 404)
    return response

def response_404_load_on_truck():
    res_json = json.dumps({
        "Error": 
        ("The specified load is not on this truck")
    }, indent=4)

    response = make_response(res_json, 404)
    return response

def response_405():
    res_json = json.dumps({
        "Error": 
        "Request method not allowed"
    }, indent=4)

    response = make_response(res_json, 405)
    response.headers.set("Allow", ["POST", "GET"])
    return response

def response_406():
    res_json = json.dumps({
        "Error": 
        "Request Accept header has a MIME type that is not supported"
    }, indent=4)

    response = make_response(res_json, 406)
    return response

def response_415():
    res_json = json.dumps({
        "Error": 
        "Request must be in application/json format"
    }, indent=4)

    response = make_response(res_json, 415)
    return response

