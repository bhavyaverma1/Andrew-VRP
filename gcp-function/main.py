from classes import *
from helper_functions import *
from solver import *

import functions_framework
import pandas as pd
import numpy as np
import datetime, time
import random
random.seed(2022)

# for configurations
from dotenv import load_dotenv
import sys, os, re, math
load_dotenv()
import json 

# for distance matrix
import googlemaps
from haversine import haversine
from scipy.spatial.distance import cdist

# for routing
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

import warnings
warnings.filterwarnings('ignore')


@functions_framework.http
def run(request):
  # DATA HANDLING
  plan_date = datetime.date.today() # or you can do datetime.date(year,month,day) where you specify the year month day
  request_json = request.get_json(silent=True)

  try:    
    # Load JSON settings and data
    settings = request_json.get('settings')
    data = pd.json_normalize(request_json.get('data')).replace('', np.nan) if 'data' in request_json else pd.DataFrame()
    coordinates_str = settings['INSTALLER_END_COORDS']
    num_vehicles_str = settings['NUM_INSTALLERS']
    num_days_str = settings['NUM_DAYS']

    try:
      os.environ['MAX_TRAVEL_DISTANCE'] = settings['MAX_TRAVEL_DISTANCE']
      os.environ['START_TIME_OF_DAY'] = settings['START_TIME_OF_DAY']
      os.environ['NUM_SOLUTIONS'] = settings['NUM_SOLUTIONS']
      os.environ['TOTAL_LOAD_WEIGHTAGE'] = settings['TOTAL_LOAD_WEIGHTAGE']
      os.environ['TOTAL_DISTANCE_WEIGHTAGE'] = settings['TOTAL_DISTANCE_WEIGHTAGE']
      print('I AM HERE WITH MY ENV VARIBALES CODE BLOCK')
    except Exception as ee:
      print("Default env variables being used because an error occurred:", str(ee))

    # Num of days variable
    if num_days_str=='' or num_days_str==None:
      num_days = 3
    else:
      num_days = int(num_days_str)

    # Num of vehicles variable
    if num_vehicles_str=='' or num_vehicles_str==None:
      num_vehicles = 4
    else:
      num_vehicles = int(num_vehicles_str)
    
    # Installer end locations variable
    if coordinates_str=='' or coordinates_str==None:
      num_vehicles = 4
      ins_ends_coords = [(-34.8218243,138.7292797),(-34.8104796,138.6111791),(-34.8938435,138.6918266),(-34.7810071,138.6461490)] # Set the last installer which is a team .. its endlocation to factory
    else:
      coordinates_tuples = eval(coordinates_str)
      ins_ends_coords = [tuple(map(float, coord)) for coord in coordinates_tuples]
      print('I AM HERE WITH MY SUCCESSFUL READ OF COORD END LOCATIONS')

  except Exception as e:
    print("Default settings being used because an error occurred:", str(e))
    data = pd.json_normalize(request_json.get('data')).replace('', np.nan) if 'data' in request_json else pd.DataFrame()
    num_days = 3
    num_vehicles = 4
    ins_ends_coords = [(-34.8218243,138.7292797),(-34.8104796,138.6111791),(-34.8938435,138.6918266),(-34.7810071,138.6461490)] # Set the last installer which is a team .. its endlocation to factory

  data_output = data
  current_day = plan_date
  print('HALLLOOO')
  print(os.getenv('MAX_TRAVEL_DISTANCE'))
  print(os.getenv('NUM_SOLUTIONS'))
  for i in range(num_days):
      # print('Planning Day:',i+1)
      current_day = next_working_date(current_day)
      routes, total_distance, total_load, job_times, data_output = solve(data_output, current_day, num_vehicles, ins_ends_coords)

  print(data_output.head(3))
  json_data = data_output.to_json(orient='records')

  return json_data
