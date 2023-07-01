# import ast
# one_ins_coordinates_str = "(-34.67377397281624, 138.7048092399703),(-34.84104058393277, 138.65651009764483),(-34.82263128787697, 138.72475029764425),(-34.85469027275228, 138.6698013688102),(-34.80905685768566, 138.66489415995585),(-34.65115832516502, 138.67660877124322),(-34.823493893116805, 138.64916435385524),(-34.80967168741497, 138.7138570105772),(-34.896046381893775, 138.52113019393616),(-34.86777826960525, 138.67302557546506),(-34.791106268147736, 138.61402182410072),(-34.65969430453714, 138.67263588201587),(-35.01863842185395, 138.54307062709705)"
# two_ins_coordinates_str = "(-34.812053822189654, 138.61663129983626)"
# three_ins_coordinates_str = ""
# four_ins_coordinates_str = ""

# num_vehicles_str = "14"
# num_days_str ="3"

# # Num of days variable
# if num_days_str=='' or num_days_str==None:
#     num_days = 3
# else:
#     num_days = int(num_days_str)

# # Num of vehicles variable
# if num_vehicles_str=='' or num_vehicles_str==None:
#     num_vehicles = 4
# else:
#     num_vehicles = int(num_vehicles_str)

# # Installer end locations variable
# if one_ins_coordinates_str == '' or one_ins_coordinates_str is None:
#     num_vehicles = 4
#     one_ins_ends_coords = [((-34.8218243, 138.7292797), 1), ((-34.8104796, 138.6111791), 1), ((-34.8938435, 138.6918266), 1), ((-34.7810071, 138.646149), 1)] # Set the last installer which is a team .. its endlocation to factory
# else:
#     one_ins_coordinates_tuples = eval(one_ins_coordinates_str)
#     if isinstance(one_ins_coordinates_tuples, tuple):
#         print(one_ins_coordinates_tuples)
#         one_ins_ends_coords = [one_ins_coordinates_tuples]
#     else:
#         one_ins_ends_coords = [tuple(map(float, coord)) for coord in one_ins_coordinates_tuples]
#     one_ins_ends_coords = [(coord, 1) for coord in one_ins_ends_coords]


# if two_ins_coordinates_str == '' or two_ins_coordinates_str is None:
#     two_ins_ends_coords = []
# else:
#     two_ins_coordinates_tuples = eval(two_ins_coordinates_str)
#     if isinstance(two_ins_coordinates_tuples, tuple):
#         two_ins_ends_coords = [two_ins_coordinates_tuples]
#     else:
#         two_ins_ends_coords = [tuple(map(float, coord)) for coord in two_ins_coordinates_tuples]
#     two_ins_ends_coords = [(coord, 2) for coord in two_ins_ends_coords]

# if three_ins_coordinates_str == '' or three_ins_coordinates_str is None:
#     three_ins_ends_coords = []
# else:
#     three_ins_coordinates_tuples = eval(three_ins_coordinates_str)
#     if isinstance(three_ins_coordinates_tuples, tuple):
#         three_ins_ends_coords = [three_ins_coordinates_tuples]
#     else:
#         three_ins_ends_coords = [tuple(map(float, coord)) for coord in three_ins_coordinates_tuples]
#     three_ins_ends_coords = [(coord, 3) for coord in three_ins_ends_coords]

# if four_ins_coordinates_str == '' or four_ins_coordinates_str is None:
#     four_ins_ends_coords = []
# else:
#     four_ins_coordinates_tuples = eval(four_ins_coordinates_str)
#     if isinstance(four_ins_coordinates_tuples, tuple):
#         four_ins_ends_coords = [four_ins_coordinates_tuples]
#     else:
#         four_ins_ends_coords = [tuple(map(float, coord)) for coord in four_ins_coordinates_tuples]
#     four_ins_ends_coords = [(coord, 4) for coord in four_ins_ends_coords]

# ins_ends_coords = one_ins_ends_coords + two_ins_ends_coords + three_ins_ends_coords + four_ins_ends_coords
# if not ins_ends_coords:
#     num_vehicles = 4
#     ins_ends_coords = [
#         ((-34.8218243, 138.7292797), 1),
#         ((-34.8104796, 138.6111791), 1),
#         ((-34.8938435, 138.6918266), 1),
#         ((-34.7810071, 138.646149), 2)
#     ]  # Set the last installer which is a team ... its end location to the factory
# print(ins_ends_coords)
# dd=9/0
# print('I AM HERE WITH MY SUCCESSFUL READ OF COORD END LOCATIONS')

import ast

def check_tuple_type(string):
    try:
        evaluated = eval(string)
        if isinstance(evaluated, tuple):
            if all(isinstance(item, tuple) for item in evaluated):
                return "Tuple of tuples"
            else:
                return "Just a tuple"
        else:
            return "Not a tuple"
    except SyntaxError:
        return "Invalid syntax"


def parse_coordinates(coordinates_str):
    if not coordinates_str:
        return []

    tuple_type = check_tuple_type(coordinates_str)

    if tuple_type == "Tuple of tuples":
        coordinates = ast.literal_eval(coordinates_str)
        coordinates = list(coordinates)  # Convert tuple to list
    elif tuple_type == "Just a tuple":
        coordinates = [ast.literal_eval(coordinates_str)]
    else:
        return []

    return coordinates

one_ins_coordinates_str = "(-34.67377397281624, 138.7048092399703),(-34.84104058393277, 138.65651009764483),(-34.82263128787697, 138.72475029764425),(-34.85469027275228, 138.6698013688102),(-34.80905685768566, 138.66489415995585),(-34.65115832516502, 138.67660877124322),(-34.823493893116805, 138.64916435385524),(-34.80967168741497, 138.7138570105772),(-34.896046381893775, 138.52113019393616),(-34.86777826960525, 138.67302557546506),(-34.791106268147736, 138.61402182410072),(-34.65969430453714, 138.67263588201587),(-35.01863842185395, 138.54307062709705)"
two_ins_coordinates_str = "(-34.812053822189654, 138.61663129983626)"

one_ins_coordinates = parse_coordinates(one_ins_coordinates_str)
two_ins_coordinates = parse_coordinates(two_ins_coordinates_str)

print(one_ins_coordinates)
print(two_ins_coordinates)