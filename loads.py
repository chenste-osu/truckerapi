from datetime import date
from flask import Blueprint, request
from google.cloud import datastore
from response import *
from helpers import *
from constants import *

client = datastore.Client()

bp = Blueprint('loads', __name__, url_prefix='/loads')

@bp.route('', methods=['POST', 'GET', 'PUT', 'PATCH', 'DELETE'])
def loads_base():
    if request.method == 'POST':
        if 'application/json' not in request.accept_mimetypes:
            return response_406()

        # request validation
        content = request.get_json(silent=True)
        if content is None:
            return response_415() # must be JSON
        if not exist_load_body(content):
            return response_400_missing_loaddata() # must have all required attr
        elif not valid_full_load_body(content):
            return response_400_invalid_loaddata() # must have valid attr
            
        # upsert new load into datastore
        new_load = datastore.entity.Entity(key=client.key(loads_key))
        new_load.update({
            "volume": content["volume"],
            "item": content["item"],
            "quantity": content["quantity"],
            "carrier": None
        })
        client.put(new_load)

        # after putting the new truck in we will get the auto-generated id
        new_load["id"] = new_load.key.id
        new_load.update({
            "self": request.base_url + "/" + str(new_load.key.id)
        })
        client.put(new_load)

        return response_OK(new_load, 201)

    elif request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            return response_406()

        base_url = request.base_url
        query_limit = int(request.args.get('limit', '5'))
        query_offset = int(request.args.get('offset', '0'))

        all_paginated_loads = get_loads(base_url, query_limit, query_offset)
            
        return response_OK_json(all_paginated_loads, 200)

    elif request.method == 'PUT' \
            or request.method == 'PATCH' \
            or request.method == 'DELETE':
        return response_405()

    else:
        return 'Method not recognized'

@bp.route('/<id>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def loads_withid(id):
    if id is None or id == "":
        return response_404_load()

    # find the load
    target_load = find_load(id)
    if target_load is None:
        return response_404_load()

    if request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            return response_406()

        target_load["id"] = target_load.key.id
        return response_OK_json(target_load, 200)

    elif request.method == 'PATCH':
        if 'application/json' not in request.accept_mimetypes:
            return response_406()

        # request validation
        content = request.get_json(silent=True)
        if content is None:
            return response_415()
        if ("volume" not in content 
                and "item" not in content 
                and "quantity" not in content):
            return response_400_missing_loaddata()

        if "volume" in content:
            if valid_volume(content["volume"]):
                target_load.update({"volume": content["volume"]})
        if "item" in content:
            if valid_item(content["item"]):
                target_load.update({"item": content["item"]})
        if "quantity" in content:
            if valid_length(content["quantity"]):
                target_load.update({"quantity": content["quantity"]})

        client.put(target_load)
        target_load["id"] = target_load.key.id
        return response_OK_json(target_load, 200)

    elif request.method == 'DELETE':
        # first remove the load from the associated boat
        if target_load["carrier"]:
            related_truck_id = target_load["carrier"]["id"]
            related_truck = find_truck(related_truck_id)
            removed_load_list = [load for load in related_truck["loads"] if not (int(load['id']) == target_load.key.id)]
            related_truck.update({
                "loads": removed_load_list
            })
            client.put(related_truck)
            
        # then delete the load
        key = client.key(loads_key, int(id))
        client.delete(key)
        return response_OK(target_load, 204)

    elif request.method == 'PUT':
        return response_405()
    
    else:
        return 'Method not recognized'
