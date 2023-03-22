from LayoutGraphOptimizer.LayoutGraph import LayoutGraph, Path
import time
from LayoutGraphOptimizer.utils import *
# from find_paths import LAYOUT, WEIGHTS, VARIANT_MIXES, COLOR_MAP
# print(LAYOUT)


def test_combinatorial_time():
    LAYOUT = {
    'nodes': [
        'b', 'null','y','null','y','null','g',
        'y', 'null', 'y','null','null','null', 'y',
        'null','null','null','null','null','null','g',
        'null','null','null','null','null','null','b',
        'g', 'null','g','null', 'null','null','null',
        'g', 'null','g','null', 'b','null','null'
    ],
    'length_x': 7,
    'length_y': 6
    }

    # Define weights (i.e. processing time) for each node type (including null)
    WEIGHTS = {
        'b': 3,
        'y': 3,
        'g': 5,
        'null': 1,
    }

    # Set colors for nodes, which is needed for plotting the graph. Note that each you need to define the color for each 
    #   node type (including null) as well as the 'start' and 'end' node types.
    COLOR_MAP = {
        'start': 'black',
        'b': 'blue',
        'y': 'darkgoldenrod',
        'g': 'green',
        'end': 'black',
        'null': 'grey'
    }

    # Variant Mix A: How many of each type of node should be traversed?
    VARIANT_MIXES = {
        'mix_a': {
            'g': 4,
            'y': 1,
            'b': 1
        },
        'mix_b': {
            'g': 0,
            'y': 0,
            'b': 1
        },
        'mix_c': {
            'g': 1,
            'y': 0,
            'b': 1
        },
        'mix_d': {
            'g': 0,
            'y': 1,
            'b': 1
        }
    }


    graphGlobal = LayoutGraph(LAYOUT, WEIGHTS)

    # Calculate the best combinations of stations for the different mixes
    combinations = {}
    combinations_new_k4 = {}
    combinations_new_k3 = {}
    combinations_new_k2 = {}
    combinations_new_k1 = {} 

    start_time_combinations_old = time.perf_counter()
    for mix_type in VARIANT_MIXES:
        # Obtaining all the valid combinations and corresponding cost
        combinations[mix_type] = graphGlobal.get_all_valid_combinations(VARIANT_MIXES[mix_type])
    total_time_combinations_old = time.perf_counter() - start_time_combinations_old

    start_time_combinations_new_k4 = time.perf_counter()
    for mix_type in VARIANT_MIXES:
        combinations_new_k4[mix_type] = graphGlobal.get_all_valid_combinations_new(VARIANT_MIXES[mix_type], k=4)
    total_time_combinations_new_k4 = time.perf_counter() - start_time_combinations_new_k4

    start_time_combinations_new_k3 = time.perf_counter()
    for mix_type in VARIANT_MIXES:
        combinations_new_k3[mix_type] = graphGlobal.get_all_valid_combinations_new(VARIANT_MIXES[mix_type], k=3)
    total_time_combinations_new_k3 = time.perf_counter() - start_time_combinations_new_k3

    start_time_combinations_new_k2 = time.perf_counter()
    for mix_type in VARIANT_MIXES:
        combinations_new_k2[mix_type] = graphGlobal.get_all_valid_combinations_new(VARIANT_MIXES[mix_type], k=2)
    total_time_combinations_new_k2 = time.perf_counter() - start_time_combinations_new_k2

    start_time_combinations_new_k1 = time.perf_counter()
    for mix_type in VARIANT_MIXES:
        combinations_new_k1[mix_type] = graphGlobal.get_all_valid_combinations_new(VARIANT_MIXES[mix_type], k=1)
    total_time_combinations_new_k1 = time.perf_counter() - start_time_combinations_new_k1

    best_combination = get_best_combination(combinations['mix_a'])
    worst_combination = get_worst_combination(combinations['mix_a'])

    best_combination_new_k4 = get_best_combination(combinations_new_k4['mix_a'])
    worst_combination_new_k4 = get_worst_combination(combinations_new_k4['mix_a'])

    best_combination_new_k3 = get_best_combination(combinations_new_k3['mix_a'])
    worst_combination_new_k3 = get_worst_combination(combinations_new_k3['mix_a'])

    best_combination_new_k2 = get_best_combination(combinations_new_k2['mix_a'])
    worst_combination_new_k2 = get_worst_combination(combinations_new_k2['mix_a'])

    best_combination_new_k1 = get_best_combination(combinations_new_k1['mix_a'])
    worst_combination_new_k1 = get_worst_combination(combinations_new_k1['mix_a'])

    print(f"<--------------------------------------------------------------------------------->")
    print('INFO FOR MIX A')
    print(f'Number of stations in mix A:        {VARIANT_MIXES["mix_a"]["g"] + VARIANT_MIXES["mix_a"]["y"] + VARIANT_MIXES["mix_a"]["b"]}')
    print("<---------------------------------------------------------------------------------->")
    print(f'{"Best combination cost":37} {best_combination.cost:<7} {"number of combinations"} {len(combinations["mix_a"]):>7}')
    print(f'{"best_combination_new k=4 cost":37} {best_combination_new_k4.cost:<7} {"number of combinations"} {len(combinations_new_k4["mix_a"]):>7}')
    print(f'{"best_combination_new k=3 cost":37} {best_combination_new_k3.cost:<7} {"number of combinations"} {len(combinations_new_k3["mix_a"]):>7}')
    print(f'{"best_combination_new k=2 cost":37} {best_combination_new_k2.cost:<7} {"number of combinations"} {len(combinations_new_k2["mix_a"]):>7}')
    print(f'{"best_combination_new k=1 cost":37} {best_combination_new_k1.cost:<7} {"number of combinations"} {len(combinations_new_k1["mix_a"]):>7}')
    print("<---------------------------------------------------------------------------------->")
    print(f'{"best_combination_old nodes":37} {best_combination.nodes}') 
    print(f'{"best_combination_new k=4 nodes":37} {best_combination_new_k4.nodes}')
    print(f'{"best_combination_new k=3 nodes":37} {best_combination_new_k3.nodes}')
    print(f'{"best_combination_new k=2 nodes":37} {best_combination_new_k2.nodes}')
    print(f'{"best_combination_new k=1 nodes":37} {best_combination_new_k1.nodes}')
    print("<---------------------------------------------------------------------------------->")
    print(f'{"Execution time combinations_old":37} {total_time_combinations_old:.2f}s')
    print(f'{"Execution time combinations_new k=4":37} {total_time_combinations_new_k4:.2f}s')
    print(f'{"Execution time combinations_new k=3":37} {total_time_combinations_new_k3:.2f}s')
    print(f'{"Execution time combinations_new k=2":37} {total_time_combinations_new_k2:.2f}s')
    print(f'{"Execution time combinations_new k=1":37} {total_time_combinations_new_k1:.2f}s')


if __name__ == "__main__":
    test_combinatorial_time()