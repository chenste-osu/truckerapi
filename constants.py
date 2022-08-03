from os import environ as env
from dotenv import find_dotenv, load_dotenv

owners_key = "owners"
trucks_key = "trucks"
loads_key = "loads"


ALGORITHMS = ["RS256"]

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

CLIENT_ID = env.get("AUTH0_CLIENT_ID")
CLIENT_SECRET = env.get("AUTH0_CLIENT_SECRET")
DOMAIN = env.get("AUTH0_DOMAIN")
SECRET_KEY = env.get("APP_SECRET_KEY")