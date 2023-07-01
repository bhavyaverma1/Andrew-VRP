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
    one_ins_coordinates_str = settings['ONE_INSTALLER_END_COORDS']
    two_ins_coordinates_str = settings['TWO_INSTALLER_END_COORDS']
    three_ins_coordinates_str = settings['THREE_INSTALLER_END_COORDS']
    four_ins_coordinates_str = settings['FOUR_INSTALLER_END_COORDS']
    five_ins_coordinates_str = settings['FIVE_INSTALLER_END_COORDS']
    six_ins_coordinates_str = settings['SIX_INSTALLER_END_COORDS']

    num_vehicles_str = settings['NUM_INSTALLERS']
    num_days_str = settings['NUM_DAYS']

    try:
      os.environ['FACTORY_GEO_COORD'] = settings['FACTORY_GEO_COORD']
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
    if one_ins_coordinates_str == '' or one_ins_coordinates_str is None:
      num_vehicles = 4
      one_ins_ends_coords = [((-34.8218243, 138.7292797), 1), ((-34.8104796, 138.6111791), 1), ((-34.8938435, 138.6918266), 1), ((-34.7810071, 138.646149), 1)] # Set the last installer which is a team .. its endlocation to factory
    else:
      one_ins_coordinates = parse_coordinates(one_ins_coordinates_str)
      one_ins_ends_coords = [tuple(map(float, coord)) for coord in one_ins_coordinates]
      one_ins_ends_coords = [(coord, 1) for coord in one_ins_ends_coords]

    if two_ins_coordinates_str == '' or two_ins_coordinates_str is None:
      two_ins_ends_coords = []
    else:
      two_ins_coordinates = parse_coordinates(two_ins_coordinates_str)
      two_ins_ends_coords = [tuple(map(float, coord)) for coord in two_ins_coordinates]
      two_ins_ends_coords = [(coord, 2) for coord in two_ins_ends_coords]

    if three_ins_coordinates_str == '' or three_ins_coordinates_str is None:
      three_ins_ends_coords = []
    else:
      three_ins_coordinates = parse_coordinates(three_ins_coordinates_str)
      three_ins_ends_coords = [tuple(map(float, coord)) for coord in three_ins_coordinates]
      three_ins_ends_coords = [(coord, 3) for coord in three_ins_ends_coords]

    if four_ins_coordinates_str == '' or four_ins_coordinates_str is None:
      four_ins_ends_coords = []
    else:
      four_ins_coordinates = parse_coordinates(four_ins_coordinates_str)
      four_ins_ends_coords = [tuple(map(float, coord)) for coord in four_ins_coordinates]
      four_ins_ends_coords = [(coord, 4) for coord in four_ins_ends_coords]
    
    if five_ins_coordinates_str == '' or five_ins_coordinates_str is None:
      five_ins_ends_coords = []
    else:
      five_ins_coordinates = parse_coordinates(five_ins_coordinates_str)
      five_ins_ends_coords = [tuple(map(float, coord)) for coord in five_ins_coordinates]
      five_ins_ends_coords = [(coord, 5) for coord in five_ins_ends_coords]
    
    if six_ins_coordinates_str == '' or six_ins_coordinates_str is None:
      six_ins_ends_coords = []
    else:
      six_ins_coordinates = parse_coordinates(six_ins_coordinates_str)
      six_ins_ends_coords = [tuple(map(float, coord)) for coord in six_ins_coordinates]
      six_ins_ends_coords = [(coord, 6) for coord in six_ins_ends_coords]

    ins_ends_coords = one_ins_ends_coords + two_ins_ends_coords + three_ins_ends_coords + four_ins_ends_coords + five_ins_ends_coords + six_ins_ends_coords
    if not ins_ends_coords:
        num_vehicles = 4
        ins_ends_coords = [
            ((-34.8218243, 138.7292797), 1),
            ((-34.8104796, 138.6111791), 1),
            ((-34.8938435, 138.6918266), 1),
            ((-34.7810071, 138.646149), 1)
        ]
    print(ins_ends_coords)
    print('I AM HERE WITH MY SUCCESSFUL READ OF COORD END LOCATIONS')

  except Exception as e:
    print("Default settings being used because an error occurred:", str(e))
    data = pd.json_normalize(request_json.get('data')).replace('', np.nan) if 'data' in request_json else pd.DataFrame()
    num_days = 3
    num_vehicles = 4
    ins_ends_coords = [((-34.8218243, 138.7292797), 1), ((-34.8104796, 138.6111791), 1), ((-34.8938435, 138.6918266), 1), ((-34.7810071, 138.646149), 1)] # Set the last installer which is a team .. its endlocation to factory

  data_output = data
  current_day = plan_date

  for i in range(num_days):
      # print('Planning Day:',i+1)
      current_day = next_working_date(current_day)
      routes, total_distance, total_load, job_times, data_output = solve(data_output, current_day, num_vehicles, ins_ends_coords)

  print(data_output.head(3))
  json_data = data_output.to_json(orient='records')

  return json_data
