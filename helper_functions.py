import os
import requests, json
import googlemaps
from dotenv import load_dotenv

load_dotenv()

factory_coord = os.getenv("FACTORY_GEO_COORD") 
api_key = os.getenv("API_KEY")

gmaps = googlemaps.Client(key=api_key)

def get_distance(origin,destination):
    return gmaps.distance_matrix(origin,destination)['rows'][0]['elements'][0]['distance']['value']

def get_travel_time(origin,destination):
    return gmaps.distance_matrix(origin,destination)['rows'][0]['elements'][0]['duration']['value']



