from classes import *
from helper_functions import *
from solver import *

import pandas as pd
import numpy as np
import datetime, time
import random
random.seed(2022)

# for configurations
from dotenv import load_dotenv
import sys, os, re, math
load_dotenv()

# for distance matrix
import gmaps
import googlemaps
from haversine import haversine
from scipy.spatial.distance import cdist

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

# for routing
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from IPython.display import display
import warnings
warnings.filterwarnings('ignore')

## DATA HANDLING
file_path = '../data/processed_data_10.csv'
plan_date = datetime.date.today() # or you can do datetime.date(year,month,day)
num_vehicles = 4
ins_ends_coords = [(-34.8218243,138.7292797),(-34.8104796,138.6111791),(-34.8938435,138.6918266),(-34.7810071,138.6461490)] # Set the last installer which is a team .. its endlocation to factory
# data = pd.read_csv(file_path) # Reading the csv

# Parse command line arguments
parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
# parser.add_argument("-r", "--references", default=3, type=int, help="Number of references to include")
parser.add_argument("filename", help="Path to the file")
args = vars(parser.parse_args())

data = pd.read_csv(args['filename']) # Reading the csv

num_days = 3
data_output = data
current_day = plan_date

for i in range(num_days):
    # print('Planning Day:',i+1)
    current_day = next_working_date(current_day)
    routes, total_distance, total_load, job_times, data_output = solve(data_output, current_day, num_vehicles, ins_ends_coords)

data_output.to_csv('output/data_output.csv',index=False)