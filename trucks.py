from re import L
from flask import Blueprint, request
from google.cloud import datastore
from response import *
from helpers import *
from constants import *

client = datastore.Client()

bp = Blueprint('trucks', __name__, url_prefix='/trucks')

@bp.route('', methods=['POST', 'GET', 'PUT', 'PATCH', 'DELETE'])
def trucks_base():
    if request.method == 'POST':
        if 'application/json' not in request.accept_mimetypes:
            return response_406()

        # check for valid JWT - required
        payload = verify_jwt(request)

        search_owner = find_owner(payload["sub"])
        if search_owner is None:
            return response_404_owner()

        # request validation
        content = request.get_json(silent=True)
        if content is None:
            return response_415() # must be JSON
        if not exist_truck_body(content):
            return response_400_missing_truckdata() # must have all required attr
        elif not valid_full_truck_body(content):
            return response_400_invalid_truckdata() # must have valid attr

        # upsert new truck into datastore
        new_key = client.key(trucks_key)
        new_truck = datastore.entity.Entity(key=new_key)
        new_truck.update({
            "name": content["name"], 
            "type": content["type"],
            "length": content["length"],
            "owner": payload["sub"],
            "public": content["public"],
            "loads": []
        })
        client.put(new_truck)

        # after putting the new truck in we will get the auto-generated id
        new_truck["id"] = new_truck.key.id
        new_truck.update({
            "self": request.base_url + "/" + str(new_truck.key.id)
        })
        client.put(new_truck)

        # return response as json
        return response_OK_created(new_truck, 201)

    elif request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            return response_406()

        base_url = request.base_url
        query_limit = int(request.args.get('limit', '5'))
        query_offset = int(request.args.get('offset', '0'))

        # if there is no jwt, then display all public trucks
        if 'Authorization' not in request.headers:
            public_trucks = get_trucks(base_url, query_limit, query_offset, False)
            return response_OK_json(public_trucks, 200)

        payload = verify_jwt(request)

        # check if owner exists based on jwt
        search_owner = find_owner(payload["sub"])
        if search_owner is None:
            return response_404_owner()

        owner_trucks = get_trucks(base_url, query_limit, query_offset, True, payload["sub"])
        return response_OK_json(owner_trucks, 200)
        
    # unsupported methods - cannot edit or delete the entire resource
    elif request.method == 'PUT' \
            or request.method == 'PATCH' \
            or request.method == 'DELETE':
        return response_405()

    else:
        return 'Method not recognized'

@bp.route('/<id>', methods=['POST', 'GET', 'PATCH', 'PUT', 'DELETE'])
def trucks_withid(id):
    if id is None or id == "":
        return response_404_truck()

    # find the truck
    target_truck = find_truck(id)
    if target_truck is None:
        return response_404_truck()
    
    if request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            return response_406()

        # if truck is public then just display it
        if target_truck["public"]:
            target_truck["id"] = target_truck.key.id
            return response_OK_json(target_truck, 200)
        # otherwise require valid jwt to display private truck
        else:
            payload = verify_jwt(request)
            owner = payload["sub"]
            if owner != target_truck["owner"]:
                return response_403_truck()
            target_truck["id"] = target_truck.key.id
            return response_OK_json(target_truck, 200)

    if request.method == 'PATCH':
        if 'application/json' not in request.accept_mimetypes:
            return response_406()

        # valid jwt is required to edit truck
        payload = verify_jwt(request)
        owner = payload["sub"]
        if owner != target_truck["owner"]:
            return response_403_truck()

        # request validation
        content = request.get_json(silent=True)
        if content is None:
            return response_415()
        if ("name" not in content 
                and "type" not in content 
                and "length" not in content 
                and "public" not in content):
            return response_400_missing_truckdata()
        
        if "name" in content:
            if valid_name(content["name"]):
                target_truck.update({"name": content["name"]})
        if "type" in content:
            if valid_type(content["type"]):
                target_truck.update({"type": content["type"]})
        if "length" in content:
            if valid_length(content["length"]):
                target_truck.update({"length": content["length"]})
        if "public" in content:
            if valid_length(content["public"]):
                target_truck.update({"public": content["public"]})

        client.put(target_truck)
        target_truck["id"] = target_truck.key.id
        return response_OK_json(target_truck, 200)

    if request.method == 'DELETE':
        payload = verify_jwt(request)
        owner = payload["sub"]
        if owner != target_truck["owner"]:
            return response_403_truck()

        key = client.key(trucks_key, int(id))
        client.delete(key)
        # update all loads that had this truck as a carrier
        del_truck_in_loads(id)

        return response_OK(target_truck, 204)

    # unsupported methods
    elif request.method == 'PUT':
        return response_405()

    else:
        return 'Method not recognized'

# this route is unprotected and does not require jwt auth
@bp.route('/<truckid>/loads/<loadid>', methods=['GET', 'PATCH', 'PUT', 'DELETE'])
def assign_truck_load(truckid, loadid):
    if id is None or id == "":
        return response_404_both()

    search_results = find_load_and_truck(loadid, truckid)
    if search_results["found_load"] is None \
            or search_results["found_truck"] is None:
        if request.method == 'PUT':
            return response_404_both()
        elif request.method == 'DELETE':
            return response_404_both()

    target_truck = search_results["found_truck"]
    target_load = search_results["found_load"]

    if request.method == 'PUT':
        if target_load["carrier"]:
            return response_403_load()

        # in target_LOAD: assign specified boat
        target_load.update({
            "carrier": {
                "id": target_truck.key.id,
                "name": target_truck["name"],
                "type": target_truck["type"],
                "length": target_truck["length"],
                "public": target_truck["public"],
                "self": target_truck["self"]
            }
        })
        # in target_TRUCK: append current load to the list of loads
        target_truck["loads"].append({
            "id": target_load.key.id,
            "volume": target_load["volume"],
            "item": target_load["item"],
            "quantity": target_load["quantity"],
            "self": target_load["self"]
        })

        client.put(target_load)
        client.put(target_truck)

        return response_OK_json(target_truck, 204)

    elif request.method == 'DELETE':
        load_on_truck = False

        # search the truck's load list
        for load_index in range(0, len(target_truck["loads"])):
            if target_truck["loads"][load_index]["id"] == target_load.key.id:
                load_on_truck = True
                del target_truck["loads"][load_index]

        if load_on_truck is False:
            return response_404_load_on_truck()

        # update the truck and load
        client.put(target_truck) 
        target_load.update({
            "carrier": None
        })
        client.put(target_load)

        return response_OK_json(target_truck, 204)

    else:
        return 'Method not recognized'
