from flask import Blueprint, request
from google.cloud import datastore
from response import *
from helpers import *
from constants import owners_key

client = datastore.Client()

bp = Blueprint('owners', __name__, url_prefix='/owners')

@bp.route('', methods=['GET'])
def owners_base():
    if request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            return response_406()
            
        # get the entire collection of users
        query = client.query(kind=owners_key)

        owners_results = list(query.fetch())
        for owner in owners_results:
            owner["id"] = owner.key.id_or_name

        return response_OK_json(owners_results, 200)
    
    else:
        return 'Method not recognized'

@bp.route('/<id>', methods=['GET'])
def owners_withid(id):
    if request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            return response_406()

        search_owner = find_owner(id)
        if search_owner is None:
            return response_404_owner()

        return response_OK_json(search_owner, 200)

