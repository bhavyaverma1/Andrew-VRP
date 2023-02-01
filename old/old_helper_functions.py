import os
import requests, json
import googlemaps
import urllib.request
from dotenv import load_dotenv
import datetime

#for routing
import haversine as hs
import gmaps
import googlemaps
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
load_dotenv()

FACTORY_GEO_COORD = os.getenv("FACTORY_GEO_COORD") 
API_KEY = os.getenv("API_KEY")

gmaps = googlemaps.Client(key=API_KEY)

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
    return (gmaps.distance_matrix(location,FACTORY_GEO_COORD)['rows'][0]['elements'][0]['duration']['value'])//60 # ( in minutes )

def create_distance_matrix(addresses):
    # Distance Matrix API only accepts 100 elements per request, so get rows in multiple requests.
    max_elements = 100
    num_addresses = len(addresses) 
    # Maximum number of rows that can be computed per request
    max_rows = max_elements // num_addresses
    # num_addresses = q * max_rows + r.
    q, r = divmod(num_addresses, max_rows)
    print(max_rows,q,r)
    dest_addresses = addresses
    distance_matrix = []
    # Send q requests, returning max_rows rows per request.
    for i in range(q):
        origin_addresses = addresses[i * max_rows: (i + 1) * max_rows]
        response = send_request(origin_addresses, dest_addresses, API_KEY)
        distance_matrix += build_distance_matrix(response)

    # Get the remaining remaining r rows, if necessary.
    if r > 0:
        origin_addresses = addresses[q * max_rows: q * max_rows + r]
        response = send_request(origin_addresses, dest_addresses, API_KEY)
        distance_matrix += build_distance_matrix(response)
    return distance_matrix

def send_request(origin_addresses, dest_addresses, API_key):
    """ Build and send request for the given origin and destination addresses."""
    def build_address_str(addresses):
    # Build a pipe-separated string of addresses
        address_str = ''
        for i in range(len(addresses) - 1):
            address_str += str(addresses[i][0]) + ',' + str(addresses[i][1]) + '|'
        address_str += str(addresses[-1][0]) + ',' + str(addresses[-1][1])
        return address_str

    request = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial'
    origin_address_str = build_address_str(origin_addresses)
    dest_address_str = build_address_str(dest_addresses)
    request = request + '&origins=' + origin_address_str + '&destinations=' + \
                        dest_address_str + '&key=' + API_KEY
    jsonResult = urllib.request.urlopen(request).read()
    response = json.loads(jsonResult)
    print('nice')
#     print("\n",response,"\n")
    return response

def build_distance_matrix(response):
    distance_matrix = []
    for row in response['rows']:
        row_list = [row['elements'][j]['distance']['value'] for j in range(len(row['elements']))]
        distance_matrix.append(row_list)
    return distance_matrix

def build_dist_mat(factory, jobs, measure='distance'):
    gmaps_services = googlemaps.Client(key=API_KEY)
    locations= [factory] + jobs # Having complete list of relevant coordinates with factory as the first location
    origins = destinations = [item['location'] for item in [factory] + jobs]
    dm_response = gmaps_services.distance_matrix(origins=origins, destinations=destinations)
    dm_rows = [row['elements'] for row in dm_response['rows']]
    distance_matrix = [[item[measure]['value'] for item in dm_row] for dm_row in dm_rows]
    return distance_matrix

"""Vehicles Routing Problem (VRP)."""
def create_data_model(distance_matrix, num_vehicles):
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = distance_matrix
    data['num_vehicles'] = num_vehicles
    data['depot'] = 0
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

def print_solution(num_vehicles, manager, routing, solution):
    """Prints solution on console."""
    max_route_distance = 0
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        while not routing.IsEnd(index):
            plan_output += ' {} -> '.format(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        plan_output += '{}\n'.format(manager.IndexToNode(index))
        plan_output += 'Cost of the route: {}\n'.format(route_distance)
        print(plan_output)
        max_route_distance = max(route_distance, max_route_distance)
    print('Maximum route cost: {}'.format(max_route_distance))

def generate_solution(data, manager, routing):  
    """Solve the CVRP problem."""
    
    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = 'Distance'
    flattened_distance_matrix = [i for j in data['distance_matrix'] for i in j]
    max_travel_distance = int(2*max(flattened_distance_matrix))
    print(max_travel_distance)

    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        190,  # vehicle maximum travel distance
#         max_travel_distance,  # vehicle maximum travel distance
        True,  # start cumul to zero
        dimension_name)
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    print("Solver status: ", routing.status())

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)
    return solution

def solve_vrp_for(distance_matrix, num_vehicles):
    # Instantiate the data problem.
    data = create_data_model(distance_matrix, num_vehicles)

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']), data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Solve the problem
    solution = generate_solution(data, manager, routing)
    
    if solution:
        # Print solution on console.
        print_solution(num_vehicles, manager, routing, solution)
        routes = extract_routes(num_vehicles, manager, routing, solution)
        return routes
    else:
        print('No solution found.')
