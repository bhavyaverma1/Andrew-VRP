import sys, os, copy
import requests, json
import urllib.request

from dotenv import load_dotenv
load_dotenv()
import datetime

#for routing
import numpy as np
from haversine import haversine
from scipy.spatial.distance import cdist
import gmaps
import googlemaps
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

FACTORY_GEO_COORD = os.getenv("FACTORY_GEO_COORD") 
API_KEY = os.getenv("API_KEY")

gmaps_client = googlemaps.Client(key=API_KEY)
    
def get_distance(origin,destination):
    return gmaps_client.distance_matrix(origin,destination)['rows'][0]['elements'][0]['distance']['value']

def get_travel_time(origin,destination):
    return np.ceil((gmaps_client.distance_matrix(origin,destination)['rows'][0]['elements'][0]['duration']['value'])/60) # ( in minutes )

def time_to_minutes(time):
    d1 = datetime.datetime.strptime(time, '%H:%M')
    d1_delta=datetime.timedelta(hours=d1.hour,minutes=d1.minute)
    return int(d1_delta.total_seconds()/60)

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
    return (gmaps_client.distance_matrix(location,FACTORY_GEO_COORD)['rows'][0]['elements'][0]['duration']['value'])//60 # ( in minutes )

def get_distance_time_matrices(df_pending):
    dist_matrix = cdist(df_pending, df_pending, metric=haversine)
    dist_matrix = [[int(np.ceil(i*1.27)) for i in inner] for inner in dist_matrix] # Typecasting to int
    time_matrix = np.ceil(np.array(dist_matrix)*1.52)     # taking average vehicle speed to be ~40 for a straight line traversal  
    time_matrix = np.int_(time_matrix).tolist()
    for i in range(len(time_matrix)):
        for j in range(len(time_matrix[0])):
            if time_matrix[i][j]>80:
                time_matrix[i][j] = int(time_matrix[i][j]/1.13)
    return dist_matrix,time_matrix



"""Vehicles Routing Problem (VRP)."""
def create_data_model(time_matrix, num_vehicles, demands, penalties, end_locations, pref_dates, pref_days, pref_installers, pref_time_windows, plan_date, job_ids, installers_req):
    """Stores the data for the problem."""
    data = {}
    data['time_matrix'] = time_matrix
    data['demands'] = demands
    data['penalties'] = penalties
    data['num_vehicles'] = num_vehicles
    data['starts'] = [0] * data['num_vehicles']
    data['ends'] = end_locations
    data['pref_dates'] = pref_dates
    data['pref_days'] = pref_days
    data['pref_installers'] = pref_installers
    data['pref_time_windows'] = pref_time_windows
    data['plan_date'] = plan_date
    data['job_ids'] = job_ids
    data['installers_req'] = installers_req
    return data

def extract_routes(num_vehicles, manager, routing, solution):
    routes = {}
    for vehicle_id in range(num_vehicles):
        routes[vehicle_id] = []
        index = routing.Start(vehicle_id)
        while not routing.IsEnd(index):
            routes[vehicle_id].append(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
        routes[vehicle_id].append(manager.IndexToNode(index))
    return routes

def get_distance_load_times(data, manager, routing, solution):
    """Prints assignment on console."""    
    job_times = {}
    time_dimension = routing.GetDimensionOrDie('Distance')
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route_distance = 0
        route_load = 0
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]
            previous_index = index
            start_time = solution.Value(time_var)
            end_time = solution.Value(time_var) + data['demands'][node_index]
            if index != routing.Start(vehicle_id):
                job_times[data["job_ids"][node_index]] = {'start_time':start_time,'end_time':end_time,'installer_id':vehicle_id}
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        total_distance += route_distance
        total_load += route_load
    return total_distance, total_load, job_times

def print_solution(data, manager, routing, solution):
    """Prints assignment on console."""
    print(f'Planning Date: {data["plan_date"]}')
#     print(f'Objective: {solution.ObjectiveValue()}')
    # Display dropped nodes.
    dropped_nodes = 'Dropped nodes: '
    for node in range(routing.Size()):
        if routing.IsStart(node) or routing.IsEnd(node):
            continue
        if solution.Value(routing.NextVar(node)) == node:
            dropped_nodes += '{},'.format(manager.IndexToNode(node))
    print(dropped_nodes)
    
    # Display routes
    time_dimension = routing.GetDimensionOrDie('Distance')
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route_load = 0
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]
            plan_output += ' ID:{0}, Time:'.format(data["job_ids"][node_index])
            previous_index = index
            start_time = solution.Value(time_var)
            end_time = solution.Value(time_var)+ data['demands'][node_index]
            plan_output += f'({start_time}-{end_time}) -> '
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        plan_output += ' Ins_End {0} @ ({1}min)\n'.format(vehicle_id,
                                                 route_distance)
        plan_output += 'Total time spent: {}min\n'.format(route_distance)
        plan_output += 'Total job time spent: {}min\n'.format(route_load)
        print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print('Total time spent of all routes: {}min'.format(total_distance))
    print('Total job_time spent of all routes: {}min'.format(total_load))
    
def generate_solution(data, manager, routing):  
    """Solve the CVRP problem."""
    
    # Create and register a transit callback.
    def transit_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['time_matrix'][from_node][to_node] + data['demands'][from_node]

    transit_callback_index = routing.RegisterTransitCallback(transit_callback)
    
    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Add Time constraint.
    dimension_name = 'Distance'
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        480,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    
    # Allow to drop nodes.
    base_penalty = 1500
    for node in range(0, len(data['time_matrix'])):
        if(node in data['starts'] or node in data['ends']):
            continue
        else:
            ## [[ START -- HANDLING DATE AND DAY CONSTRAINTS ]]
            if data['pref_dates'][node]!=None:
                if data['pref_dates'][node]== data['plan_date']: # plan date
#                     print('Hooray',node, data['pref_dates'][node])
                    curr_penalty = 999999
                else:
                    ## code to skip a node 
                    for i in range(len(data['time_matrix'])):
                        if i ==node:
                            continue
                        data['time_matrix'][i][node], data['time_matrix'][node][i] = 99999, 99999                        
                    curr_penalty = 0
                    
            elif data['pref_days'][node]!=None:
                curr_pref_day = int(data['pref_days'][node])%7
                if curr_pref_day == data['plan_date'].weekday(): #plan_date.weekday()
#                    print('Hooday',data['job_ids'][node],data['pref_days'][node])
                    curr_penalty = 999999
                else:
                    ## code to skip a node 
                    for i in range(len(data['time_matrix'])):
                        if i ==node:
                            continue
                        data['time_matrix'][i][node], data['time_matrix'][node][i] = 99999, 99999                        
                    curr_penalty = 0
                    
            ## [[ END -- HANDLING DATE AND DAY CONSTRAINTS ]]
            else:
                if data['penalties'][node] > 0:
                    curr_penalty = base_penalty - 100*int(data['penalties'][node])
                    curr_penalty = max(curr_penalty,0)
                else:
                    curr_penalty = base_penalty - 100*int(data['penalties'][node])
#             print(node, data['pref_dates'][node], curr_penalty, data['penalties'][node])
            # print(node, curr_penalty)
            routing.AddDisjunction([manager.NodeToIndex(node)], curr_penalty)
    
    # HANDLE SPECIFIC INSTALLER CONSTRAINT
    for node in range(0, len(data['time_matrix'])):
        if(node in data['starts'] or node in data['ends']):
            continue
        else:
            if data['pref_installers'][node]!=None:
                if data['num_vehicles']>0:
                    curr_pref_installer = int(data['pref_installers'][node])%data['num_vehicles']
#                     print(node,curr_pref_installer)
                    routing.VehicleVar(manager.NodeToIndex(node)).SetValues([-1, curr_pref_installer])
                    
    # HANDLE TIME WINDOW CONSTRAINT
    for node in range(0, len(data['time_matrix'])):
        if(node in data['starts'] or node in data['ends']):
            continue
        else:
            if data['pref_time_windows'][node]!=None:
                pref_start_time = data['pref_time_windows'][node][0]-480
                pref_end_time = data['pref_time_windows'][node][1]-480
#                 print(node,pref_start_time, pref_end_time)
                distance_dimension.CumulVar(manager.NodeToIndex(node)).SetRange(pref_start_time, pref_end_time)
    
    # HANDLE MULTIPLE INSTALLER CONSTRAINT
    installers_1= []
    for vehicle_id in range(data['num_vehicles']):
        if vehicle_id == data['num_vehicles']-1:
            continue
        installers_1.append(vehicle_id)
    installers_2= [data['num_vehicles']-1]
    for node in range(0, len(data['time_matrix'])):
        if(node in data['starts'] or node in data['ends']):
            continue
        else:
            
            if data['installers_req'][node]==1:
                routing.VehicleVar(manager.NodeToIndex(node)).SetValues([-1]+installers_1)
            elif data['installers_req'][node]==2:
                routing.VehicleVar(manager.NodeToIndex(node)).SetValues([-1]+installers_2)
            else:
                print('Cant handle more than two installers currently.')

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(3)

    # Solve the problem.
    best_solution = None
    best_answer = -9999999
    for i in range(5):
        solution = routing.SolveWithParameters(search_parameters)
        if solution:
            total_distance,total_load,_ = get_distance_load_times(data, manager, routing, solution)
            curr_answer = 7*total_load - 5*total_distance # CHANGE THE WEIGHTS HERE
            if curr_answer>best_answer:
                best_solution = solution
                best_answer = curr_answer
        
    # Print solution on console.
    if best_solution:
        print_solution(data, manager, routing, best_solution)
    return best_solution

def solve_vrp_for(time_matrix_original, num_vehicles, demands, penalties, end_locations, pref_dates, pref_days, pref_installers, pref_time_windows, plan_date, job_ids, installers_req):
    # Instantiate the data problem.
    time_matrix = copy.deepcopy(time_matrix_original)
    data = create_data_model(time_matrix, num_vehicles, demands, penalties, end_locations, pref_dates, pref_days, pref_installers, pref_time_windows, plan_date, job_ids, installers_req)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data['time_matrix']), data['num_vehicles'], data['starts'], data['ends'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Solve the problem
    solution = generate_solution(data, manager, routing)
    if solution:
        routes = extract_routes(num_vehicles, manager, routing, solution)
        total_distance, total_load, job_times = get_distance_load_times(data, manager, routing, solution)
        return routes, total_distance, total_load, job_times
    else:
        print('No solution found.')
        return None,None,None,None
        
def map_solution(factory, jobs, ins_ends, routes, fig):
    colors = ['red','yellow','green','blue','#b100cd']
    for vehicle_id in routes:
        waypoints = []
        # skip depot (occupies first and last index)
        for job_index in routes[vehicle_id][1:-1]: 
            waypoints.append(jobs[job_index-1]['location'])
        installer_end_location = ins_ends[vehicle_id]['location']
        if len(waypoints) == 0:
            print('Empty route:', vehicle_id)
        else:
            route_layer = gmaps.directions_layer(
                factory['location'], waypoints[-1], waypoints=waypoints[0:-1], show_markers=False,
                stroke_color=colors[vehicle_id], stroke_weight=3, stroke_opacity=0.5)
            fig.add_layer(route_layer)
            
            # complete the route from last shipment to depot
            return_layer = gmaps.directions_layer(
                waypoints[-1], installer_end_location, show_markers=False,
                stroke_color=colors[vehicle_id], stroke_weight=3, stroke_opacity=0.5)
            fig.add_layer(return_layer)
