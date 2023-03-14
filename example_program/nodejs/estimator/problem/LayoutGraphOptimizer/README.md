# Documentation for LayoutGraphOptimizer

This Python libary provides tools to adress the path finding and placement optimization challenge by B&R Automation. It uses graphs to model the real-world scenario. It uses the Python library *networkx* for graph creation, manipulation and analyis.

## Class `LayoutGraph`

The class `LayoutGraph` is used to dynamically generate a graph representation from a given layout configuration (i.e. processing stations placed on the layout in different positions and with different characteristics). It provides features for path finding and visualizing.

### Constructor `__init()__`
The constructor of the class `LayoutGraph` will create a directed *networkx* graph object based on the input arguments given. This graph representation will model the layout of the board in the challenge together with the routing logic for moving the carts between the stations.

It takes the inputs as described below.

`layout` needs to be a dictionary in the following form:

```python
layout = {
    "nodes": ['b', 'g', 'b', 'b', 'g', 'g', 'null', 'g', 'b'],
    "length_x": 3,
    "length_y": 3
}
```

The node types (i.e. types of processing stations) are given as a list from left to right starting with the first row on the layout. The class constructor will then build the graph sequentialls based on the order of the node types and the layout size. Therefore, the first node will become a node of type `'b'` on position `(0,0)`, the second a node of type `'g'` on position `(0, 1)` and so forth.

`weights` needs to be a dictionary mapping node types to their respective weight (i.e. processing time). 

```python
weights = {
    'b': 3,
    'y': 3,
    'g': 5,
    'null': 1
}
```

### Method `find_all_paths_for_mix(...)`

*Needs to be implemented!*

### Method `find_shortest_paths_for_mix(...)`

*Needs to be implemented!*

### Method `plot_graph(color_map)`

This method plots the graph fully with nodes (i.e. positions on the layout with their a processing stations of a specific type) and edges (connections between positions on the layout based on the routing logic). 

You need to provide a dictionary `color_map` which maps node types to colors supported by *matplotlib*.



## Class `Path`

The class `Path` provides a more sophisticated representations of a path in a graph than just a mere list of nodes, e.g. the calculation of cost across nodes based on node attributes or counting the number of a specific node type in a path.