import time

# def product(*iterables):
#     if not iterables:
#         return [[]]
#     else:
#         results = []
#         for item in iterables[0]:
#             for sub_product in product(*iterables[1:]):
#                 results.append([item] + sub_product)
#         return results





# # Example usage:
# iterables = [[(0, 0), (6, 3), (4, 5)], [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)], [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)]]
# a = product(*iterables)
# for b in a:
#     print(b)

# print(f'length: {len(a)}')


import math

def euclidean_distance(point1, point2):
    return math.sqrt(sum((p1 - p2)**2 for p1, p2 in zip(point1, point2)))

def product2(distance_threshold=None, *iterables):
    if not iterables:
        return [[]]
    else:
        results = []
        for item in iterables[0]:

            for sub_product in product2(distance_threshold, *iterables[1:]):
                combination = [item] + sub_product
                
                if distance_threshold is None:
                    results.append(combination)
                else:

                    distances = [euclidean_distance(combination[i], combination[i + 1]) for i in range(len(combination) - 1)]
                    if all(distance <= distance_threshold for distance in distances):
                        results.append(combination)
        return results

# Example usage:
iterables = [[(0, 0), (6, 3), (4, 5)], [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)], [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)]]
distance_threshold = 3  # You can change this value to adjust the threshold
paths = product2(distance_threshold, *iterables)
# for path in paths:
#     print(path)

# print(f'length: {len(paths)}')


# import heapq

# def knn(point, points, k):
#     distances = [(euclidean_distance(point, other_point), other_point) for other_point in points]
#     heapq.heapify(distances)
#     return [heapq.heappop(distances)[1] for _ in range(min(k, len(distances)))]

# def product3(k=None, *iterables):
#     if not iterables:
#         return [[]]
#     else:
#         results = []
#         for item in iterables[0]:
#             neighbors = knn(item, iterables[1], k) if k is not None else iterables[1]
#             for sub_product in product3(k, *([neighbors] + iterables[2:])):
#                 results.append([item] + sub_product)
#         return results

# # Example usage:
# iterables = [[(0, 0), (6, 3), (4, 5)], [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)], [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)]]
# k = 3  # You can change this value to adjust the number of neighbors
# print(product3(k, *iterables))



import heapq
import math

# This function is used to calculate the Euclidean distance between two points
def euclidean_distance(point1, point2):
    """ Returns the Euclidean distance between two points. """
    return math.sqrt(sum((p1 - p2) ** 2 for p1, p2 in zip(point1, point2)))

def knn(point, points, k):
    """ Returns the k nearest neighbors of a point.
    
    Args:
        point: The point for which we want to find the k nearest neighbors.
        points: The list of points from which we want to find the k nearest neighbors.
        k: The number of nearest neighbors to find.
        
    Returns:
        The k nearest neighbors of the point.
    """
    # Euclidean distance is our heuristic for finding the nearest neighbors or the "best/cheapest" next step, so we use a min-heap.
    distances = [(euclidean_distance(point, other_point), other_point) for other_point in points] 
    heapq.heapify(distances)    # This is a min-heap, so the smallest distance will be at the top.
    return [heapq.heappop(distances)[1] for _ in range(min(k, len(distances)))]# Return the k nearest neighbors

def product3(k=None, *iterables):
    global a
    """ Returns the Cartesian product of the iterables.
    
    Args:
        k: The number of nearest neighbors to find for each point. k scales the number of combinations by k^N, where N is the number of iterables.
        *iterables: The iterables to take the Cartesian product of.
        
    Returns:
        The Cartesian product of the iterables.
    """
    if not iterables:
        return [[]]
    else:
        results = []
        for item in iterables[0]:
            if len(iterables) > 1:
                neighbors = knn(item, iterables[1], k) if k is not None else iterables[1]
                for sub_product in product3(k, *([neighbors] + list(iterables[2:]))):
                    results.append([item] + sub_product)

            else:
                results.append([item])
        return results

# Example usage:
iterables = [[(0, 0), (6, 3), (4, 5)],
             [(2, 0), (4, 0), (0, 1), (2, 1), (6, 1)],
             [(2, 0), (4, 0), (0, 1), (2, 1), (6, 1)], 
             [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)], 
             [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)], 
             [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)], 
             [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)], 
             [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)], 
             [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)], 
             [(6, 0), (6, 2), (0, 4), (2, 4), (0, 5), (2, 5)]]
k = 1  # You can change this value to adjust the number of neighbors
#print(product(k, *iterables))
print(f'length: {len(product3(k, *iterables))}')

time_start = time.perf_counter()
paths = product3(k, *iterables)
print(f'time: {time.perf_counter() - time_start}')

#print(a)
for path in paths:
    print(path)