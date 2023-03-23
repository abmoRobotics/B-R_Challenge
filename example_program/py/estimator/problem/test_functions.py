from LayoutGraphOptimizer.LayoutGraph import LayoutGraph, Path
import time
from LayoutGraphOptimizer.utils import *
# from find_paths import LAYOUT, WEIGHTS, VARIANT_MIXES, COLOR_MAP
# print(LAYOUT)


def test_combinatorial_time(k_range = 4):
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
    WEIGHTS = {'b': 3, 'y': 3, 'g': 5, 'null': 1}

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

    ### DEFINE GRAPH ###
    graphGlobal = LayoutGraph(LAYOUT, WEIGHTS)

    ### METRICS ###
    combinations =           [{} for i in range(k_range)]
    best_combinations =      [[] for i in range(k_range)]
    worst_combinations =     [[] for i in range(k_range)]
    timers =                 [0  for i in range(k_range)]

    ### GET ALL COMBINATIONS ###
    for k in range(1, k_range+1):
        start_time_combinations = time.perf_counter()
        for mix_type in VARIANT_MIXES:
            combinations[k-1][mix_type] = graphGlobal.find_combinations(VARIANT_MIXES[mix_type], method="knn", k=k)
        timers[k-1] = time.perf_counter() - start_time_combinations
    
    ### GET BEST AND WORST COMBINATIONS ###
    for k in range(0, k_range):
        for mix_type in VARIANT_MIXES:
            best_combinations[k].append(get_best_combination(combinations[k][mix_type]))
            worst_combinations[k].append(get_worst_combination(combinations[k][mix_type]))

    ### PRINT RESULTS ###
    print(f"<--------------------------------------------------------------------------------->")
    print('INFO FOR MIX A')
    print(f'Number of stations in mix A:        {VARIANT_MIXES["mix_a"]["g"] + VARIANT_MIXES["mix_a"]["y"] + VARIANT_MIXES["mix_a"]["b"]}')
    print("<---------------------------------------------------------------------------------->")
    for k in range(k_range-1, -1,-1):
        print(f'{"best_combination k=" + str(k+1) + " cost":37} {best_combinations[k][0].cost:<7} {"number of combinations"} {len(combinations[k]["mix_a"]):>7}')
    print("<---------------------------------------------------------------------------------->")
    for k in range(k_range-1, -1,-1):
        print(f'{"Best combination k=" + str(k+1) + " nodes":37} {best_combinations[k][0].nodes}')
    print("<---------------------------------------------------------------------------------->")
    for k in range(k_range-1, -1,-1):
        print(f'{"Worst combination k=" + str(k+1) + " nodes":37} {worst_combinations[k][0].nodes}')
    print("<---------------------------------------------------------------------------------->")
    for k in range(k_range-1, -1,-1):
        print(f'{"Execution time combinations k=" + str(k+1):37} {timers[k]:.2f}s')
    



if __name__ == "__main__":
    test_combinatorial_time()