from google.cloud import datastore
from flask import request as flask_req
from constants import *

from jose import jwt
import json

from urllib.request import urlopen

client = datastore.Client()

# AUTH ========================================================================

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

# Verify the JWT in the request's Authorization header
def verify_jwt(request):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[0]
    else:
        raise AuthError({"code": "no auth header",
                            "description":
                                "Authorization header is missing"}, 401)
    
    jsonurl = urlopen(
        "https://"+ DOMAIN + "/.well-known/jwks.json"
        )
    jwks = json.loads(jsonurl.read())

    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=CLIENT_ID,
                issuer="https://"+ DOMAIN + "/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                            "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                            "description":
                                "incorrect claims,"
                                " please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                            "description":
                                "Unable to parse authentication"
                                " token."}, 401)

        return payload
    else:
        raise AuthError({"code": "no_rsa_key",
                            "description":
                                "No RSA key in JWKS"}, 401)

# TRUCKS ======================================================================

def exist_truck_body(request_json):
    if "name" in request_json \
            and "type" in request_json \
            and "length" in request_json \
            and "public" in request_json:
        return True
    else:
        return False

def valid_full_truck_body(request_json):
    if valid_name(request_json["name"]) \
            and valid_type(request_json["type"]) \
            and valid_length(request_json["length"]) \
            and valid_public(request_json["public"]):
        return True
    else:
        return False

def unique_put_data(request_json, target_truck):
    if request_json["name"] != target_truck["name"] \
            and request_json["type"] != target_truck["type"] \
            and request_json["length"] != target_truck["length"] \
            and request_json["public"] != target_truck["public"]:
        return True
    else:
        return False

def valid_name(request_name):
    if isinstance(request_name, (str)):
        if len(request_name) < 128:
            return True
        else:
            return False
    else:
        return False

def valid_type(request_type):
    if isinstance(request_type, (str)):
        if len(request_type) < 128:
            return True
        else:
            return False
    else:
        return False

def valid_length(request_length):
    if isinstance(request_length, (int, float)):
        if request_length > 0:
            return True
        else:
            return False
    else:
        return False

def valid_public(request_public):
    if isinstance(request_public, (bool)):
        return True
    elif isinstance(request_public, (int, float)):
        return False
    else:
        return False

def find_truck(id):
    query = client.query(kind=trucks_key)
    
    trucks_results = list(query.fetch())
    for truck in trucks_results:
        if str(truck.key.id) == id:
            return truck
    return None

def find_truck_name(name):
    query = client.query(kind=trucks_key)
    trucks_results = list(query.fetch())
    for truck in trucks_results:
        if truck["name"] == name:
            return True
    return False

def get_trucks(base_url, limit, offset, show_private, owner_id=None):
    query = client.query(kind=trucks_key)

    if not show_private:
        query.add_filter("public", "=", True)
    if owner_id is not None:
        query.add_filter("owner", "=", owner_id)

    query_limit = limit
    query_offset = offset

    # count number of trucks
    num_trucks = 0
    total_trucks = list(query.fetch())
    for truck in total_trucks:
        num_trucks+=1

    truck_iterator = query.fetch(limit=query_limit, offset=query_offset)
    pages = truck_iterator.pages
    trucks_results = list(next(pages))
    if truck_iterator.next_page_token:
        next_offset = query_offset = query_limit
        next_url = base_url + "?limit=" + str(query_limit) + "&offset=" + str(next_offset)
    else:
        next_url = None

    for truck in trucks_results:
        truck["id"] = truck.key.id

    paginated_trucks = {"trucks": trucks_results}
    paginated_trucks["total_num"] = num_trucks
    if next_url:
        paginated_trucks["next"] = next_url
    
    return paginated_trucks

# LOADS =======================================================================

def exist_load_body(request_json):
    if "volume" in request_json \
            and "item" in request_json \
            and "quantity" in request_json:
        return True
    else:
        return False

def valid_full_load_body(request_json):
    if valid_volume(request_json["volume"]) \
            and valid_item(request_json["item"]) \
            and valid_quantity(request_json["quantity"]):
        return True
    else:
        return False

def valid_volume(request_volume):
    if isinstance(request_volume, (int, float)):
        if request_volume > 0:
            return True
        else:
            return False
    else:
        return False

def valid_item(request_item):
    if isinstance(request_item, (str)):
        if len(request_item) < 128:
            return True
        else:
            return False
    else:
        return False

def valid_quantity(request_quantity):
    if isinstance(request_quantity, (int, float)):
        if request_quantity > 0:
            return True
        else:
            return False
    else:
        return False

def find_load(id):
    query = client.query(kind=loads_key)
    loads_results = list(query.fetch())
    for load in loads_results:
        if str(load.key.id) == id:
            return load
    return None

def is_empty(load):
    if load["carrier"] is None:
        return True
    return False

def truck_is_at_load(load, truckid):
    if load["current_truck"] == truckid:
        return True
    return False

def find_load_and_truck(loadid, truckid):
    search_results = {
        "found_load": find_load(loadid),
        "found_truck": find_truck(truckid)
    }
    return search_results

def del_truck_in_loads(truckid):
    query = client.query(kind=loads_key)
    loads_results = list(query.fetch())

    for load in loads_results:
        if load["carrier"] is not None:
            if load["carrier"]["id"] == truckid:
                load.update({"carrier": None})
                client.put(load)

def get_loads(base_url, limit, offset):
    query = client.query(kind=loads_key)

    query_limit = limit
    query_offset = offset

    # count number of loads
    num_loads = 0
    total_loads = list(query.fetch())
    for load in total_loads:
        num_loads+=1
    
    load_iterator = query.fetch(limit= query_limit, offset=query_offset)
    pages = load_iterator.pages
    loads_results = list(next(pages))
    if load_iterator.next_page_token:
        next_offset = query_offset = query_limit
        next_url = base_url + "?limit=" + str(query_limit) + "&offset=" + str(next_offset)
    else:
        next_url = None

    for load in loads_results:
        load["id"] = load.key.id

    paginated_loads = {"loads": loads_results}
    paginated_loads["total_num"] = num_loads
    if next_url:
        paginated_loads["next"] = next_url
    

    return paginated_loads

# OWNERS ======================================================================

def find_owner(sub):
    search_key = client.key(owners_key, sub)
    query = client.query(kind=owners_key)
    query.add_filter('__key__', "=", search_key)
    owner_result = list(query.fetch())

    if owner_result:
        return owner_result[0]
    else:
        return None

def get_owner_trucks(id, show_private):
    query = client.query(kind=trucks_key)
    query.add_filter("owner", "=", id)
    if not show_private:
        query.add_filter("public", "=", True)

    trucks_results = list(query.fetch())
    for b in trucks_results:
        b["id"] = b.key.id

    return trucks_results

# ============================================================================