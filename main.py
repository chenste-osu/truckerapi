import json
import requests

from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from flask import Flask, redirect, request, render_template, session, url_for, jsonify
from google.cloud import datastore

from response import *
from helpers import *
from constants import *

import owners
import trucks
import loads

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.register_blueprint(owners.bp)
app.register_blueprint(trucks.bp)
app.register_blueprint(loads.bp)

oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    api_base_url="https://" + DOMAIN,
    access_token_url="https://" + DOMAIN + "/oauth/token",
    authorize_url="https://" + DOMAIN + "/authorize",
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=
        f'https://{DOMAIN}/.well-known/openid-configuration'
)

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

# Decode the JWT supplied in the Authorization header
@app.route('/decode', methods=['GET'])
def decode_jwt():
    payload = verify_jwt(request)
    return payload          

# LOGIN ROUTES ================================================================                               

@app.route("/")
def home():
    return render_template(
        "welcome.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )

@app.route("/userinfo", methods=["GET", "POST"])
def userinfo():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token

    searched_owner = find_owner(token["userinfo"]["sub"])
    # upsert new owner if not already in datastore
    if searched_owner is None:
        new_key = client.key(owners_key, token["userinfo"]["sub"])
        new_owner = datastore.entity.Entity(key=new_key)
        new_owner.update({
            "name": token["userinfo"]["name"], 
            "nickname": token["userinfo"]["nickname"],
            "self": request.base_url + "/owners/" + token["userinfo"]["sub"]
        })
        client.put(new_owner)
        owner_info = new_owner
        
    else:
        owner_info = searched_owner

    return render_template(
                    'userinfo.html',
                    jwt=token["id_token"],
                    user_name=token["userinfo"]["name"],
                    user_id=owner_info.key.id_or_name,
                    )

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("userinfo", _external=True)
    )

# Generate a JWT from the Auth0 domain and return it
# Request: JSON body with 2 properties with "username" and "password"
#       of a user registered with this Auth0 domain
# Response: JSON with the JWT as the value of the property id_token
@app.route('/loginpost', methods=['POST'])
def login_post():
    content = request.get_json()
    username = content["username"]
    password = content["password"]
    body = {'grant_type':'password','username':username,
            'password':password,
            'client_id':CLIENT_ID,
            'client_secret':CLIENT_SECRET
           }
    headers = { 'content-type': 'application/json' }
    url = 'https://' + DOMAIN + '/oauth/token'
    r = requests.post(url, json=body, headers=headers)
    return r.text, 200, {'Content-Type':'application/json'}

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

# =============================================================================  

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)