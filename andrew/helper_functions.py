import os
import requests, json
import googlemaps
from dotenv import load_dotenv
import datetime

load_dotenv()

factory_coord = os.getenv("FACTORY_GEO_COORD") 
api_key = os.getenv("API_KEY")

gmaps = googlemaps.Client(key=api_key)

def get_distance(origin,destination):
    return gmaps.distance_matrix(origin,destination)['rows'][0]['elements'][0]['distance']['value']

def get_travel_time(origin,destination):
    return (gmaps.distance_matrix(origin,destination)['rows'][0]['elements'][0]['duration']['value'])//60 # ( in minutes )

def next_working_date(curr_date):
    next_date = curr_date + datetime.timedelta(days=1) 
    next_date_weekday = next_date.weekday()

    # Following [[ 5 ]] day in a week work rule
    if next_date_weekday == 5: # i.e Saturday
        next_date += datetime.timedelta(days=2)
    elif next_date_weekday == 6:
        next_date += datetime.timedelta(days=1)
        
    return next_date

def get_driveback_time(location):
    return (gmaps.distance_matrix(location,factory_coord)['rows'][0]['elements'][0]['duration']['value'])//60 # ( in minutes )
