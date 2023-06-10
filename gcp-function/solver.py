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
import googlemaps
from haversine import haversine
from scipy.spatial.distance import cdist

# for routing
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import warnings
warnings.filterwarnings('ignore')

def solve(data,plan_date,num_vehicles,ins_ends_coords):
    
    ## CONFIGURATION 
    data = data.copy(deep=True)
    API_KEY = os.getenv("API_KEY") # replace api key with your own here
    FACTORY_GEO_COORD = os.getenv("FACTORY_GEO_COORD") 
    factory_coord = list(map(float,FACTORY_GEO_COORD.split(',')))
    # gmaps.configure(api_key=API_KEY)
    
    ## FILTERING ONLY 1 INSTALLER JOBS WITH STATUS = None
    jobs_installer_1 = data[(data["installers_required"].notnull()) & pd.isnull(data["status"])].reset_index(drop=True)
    
    ## PROCESSING DATA FOR VRP USE
    df_pending = jobs_installer_1[['id','Latitude','Longitude']]
    new_row = pd.DataFrame({'id':0, 'Latitude':factory_coord[0],'Longitude':factory_coord[1]}, index =[0]) # Inserting factory location to top
    df_pending = pd.concat([new_row, df_pending]).reset_index(drop=True)
    df_pending.set_index('id', inplace=True)
    df_pending['Latitude'] = df_pending['Latitude'].astype(float)
    df_pending['Longitude'] = df_pending['Longitude'].astype(float)

    for i in range(len(ins_ends_coords)):  # Inserting installers' end locations to df_pending
        ins_id = i+1
        df_pending.loc[ins_id] = [ins_ends_coords[i][0],ins_ends_coords[i][1]]
        
    # SETTING UP variables and figures for VISUALISATION
    jobs, ins_ends = [],[]
    for i, row in df_pending.iterrows():
        if i == 0:
            continue
        elif i//100 == 0: # Expecting max 100 installers for the program and job_ids no less than 100
            ins_end = { 'id': str(i), 'location': (float(row['Latitude']), float(row['Longitude']))  }
            ins_ends.append(ins_end)
        else:
            job = { 'id': str(i), 'location': (float(row['Latitude']), float(row['Longitude']))  }
            jobs.append(job)

    factory = {'location': (factory_coord[0],factory_coord[1])}
    # factory_layer = gmaps.symbol_layer([factory['location']], hover_text='Factory', info_box_content='Factory', fill_color='white', stroke_color='red', scale=6)

    job_locations = [job['location'] for job in jobs]
    job_labels = [job['id'] for job in jobs]
    # jobs_layer = gmaps.symbol_layer(
    #     job_locations, hover_text=job_labels, fill_color='white', stroke_color='black', scale=3
    # )

    ins_end_locations = [ins_end['location'] for ins_end in ins_ends]
    ins_labels = [ins_end['id'] for ins_end in ins_ends]
    # ins_ends_layer = gmaps.symbol_layer(
    #     ins_end_locations, hover_text=ins_labels, fill_color='white', stroke_color='red', scale=3
    # )

    # fig = gmaps.figure()
    # fig.add_layer(factory_layer)
    # fig.add_layer(jobs_layer)
    # fig.add_layer(ins_ends_layer)
    # # fig
    
    ## DEFINING PENALTIES AND JOB_DURATIONS(DEMANDS)
    demands, penalties = [0],[0]
    pref_dates, pref_days, pref_installers=[None],[None],[None] # first values for depot 
    pref_time_windows=[None]
    installers_req=[None]
    ## DEMANDS 
    for i in range(len(jobs)):
        if pd.isnull(jobs_installer_1.loc[i,'expected_job_time']):
            demands.append(int(60))
            continue
        demands.append(int(jobs_installer_1.loc[i,'expected_job_time']))

    ## DUE_DATE_DIFFERENCE    
    for i in range(len(jobs)):
        due_date = datetime.datetime.strptime(jobs_installer_1.loc[i,'est_installation_date'], '%d/%m/%Y').date()
        curr_date = datetime.date.today()
        due_date_diff = (due_date-curr_date).days
        penalties.append(due_date_diff)

    ## CUSTOMER PREFERRED DATE
    for i in range(len(jobs)):
        if pd.isnull(jobs_installer_1.loc[i,'pref_date']):
            pref_dates.append(None)
            continue
        pref_date_to_append = datetime.datetime.strptime(jobs_installer_1.loc[i,'pref_date'], '%d/%m/%Y').date()
        pref_dates.append(pref_date_to_append)

    ## CUSTOMER PREFERRED DAY
    for i in range(len(jobs)):
        if pd.isnull(jobs_installer_1.loc[i,'pref_day']):
            pref_days.append(None)
            continue
        pref_day_to_append = int(jobs_installer_1.loc[i,'pref_day'])
        pref_days.append(pref_day_to_append)

    ## CUSTOMER PREFERRED INSTALLER
    for i in range(len(jobs)):
        if np.isnan(jobs_installer_1.loc[i,'pref_installer']):
            pref_installers.append(None)
            continue
        pref_installers.append(int(jobs_installer_1.loc[i,'pref_installer']))

    ## CUSTOMER PREFERRED TIME WINDOWS
    for i in range(len(jobs)):
        if pd.isnull(jobs_installer_1.loc[i,'pref_time_window']):
            pref_time_windows.append(None)
            continue
        curr_pref_time_window = jobs_installer_1.loc[i,'pref_time_window'].split(',')
        curr_pref_time_window[0] = time_to_minutes(curr_pref_time_window[0])
        curr_pref_time_window[1] = time_to_minutes(curr_pref_time_window[1])
        pref_time_windows.append(curr_pref_time_window)
    
    ## MULTIPLE INSTALLERS
    for i in range(len(jobs)):
        if pd.isnull(jobs_installer_1.loc[i,'installers_required']):
            installers_req.append(None)
            continue
        installers_req.append(int(jobs_installer_1.loc[i,'installers_required']))

    ## END LOCATIONS OF INSTALLERS
    end_locations = []
    for i in range(num_vehicles):
        end_locations.append(len(jobs)+i+1)

    dist_matrix,time_matrix = get_distance_time_matrices(df_pending)
    job_ids = df_pending.index.tolist()
    
    routes, total_distance, total_load, job_times = solve_vrp_for(time_matrix, num_vehicles, demands, penalties, end_locations, pref_dates, pref_days, pref_installers, pref_time_windows, plan_date, job_ids, installers_req)
    
    ## UNCOMMENT THE CODE BELOW TO VISUALIZE THE ROUTES
    # if routes:
    #     map_solution(factory, jobs, ins_ends, routes, fig)
    # else:
    #     print('No solution found.') 
    # display(fig)
    # embed_minimal_html('export.html', views=[fig])

    # # Open the HTML file in a new tab
    # webbrowser.open_new_tab('figure.html')
    
    if job_times==None or (not job_times):
        pass
    else:
        for job_id, out_values in job_times.items():
            start_time_str = "{:02d}:{:02d}".format((out_values['start_time']//60)+8, out_values['start_time']%60)
            end_time_str = "{:02d}:{:02d}".format((out_values['end_time']//60)+8, out_values['end_time']%60)
            data.loc[data['id'] == job_id, ['installation_date','arrival_start_time','arrival_end_time','installer_ids','status']] = plan_date.strftime("%d/%m/%Y"), start_time_str, end_time_str, str(out_values['installer_id']), 'Scheduled'
    
    return routes, total_distance, total_load, job_times, data