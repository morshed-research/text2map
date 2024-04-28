import networkx as nx
import gmatch4py as gm


def dictGraph_to_networkXGraph(graph_dict):
    # Create an empty undirected graph in NetworkX
    G = nx.Graph()

    # Add nodes and edges to the graph
    for node, edges in graph_dict.items():
        G.add_node(int(node))
        for edge in edges:
            G.add_edge(int(node), int(edge))

    return G


def maximum_common_subgraph(G1_dict, G2_dict):
    # Convert the dict representations to NetworkX graphs
    G1 = dictGraph_to_networkXGraph(G1_dict)
    G2 = dictGraph_to_networkXGraph(G2_dict)

    matching_graph = nx.Graph()

    # find matching edges
    for n1,n2 in G2.edges():
        if G1.has_edge(n1, n2):
            matching_graph.add_edge(n1, n2)
    # find tha maximum connected components in matching edges
    components = nx.connected_components(matching_graph)
    largest_component = max(components, key=len)
    # create a graph from the maximum connected components in matching edges
    mcs = nx.induced_subgraph(matching_graph, largest_component)

    # calculate the domain of the equation
    input_graph_sizes = [G1.number_of_nodes() + G1.number_of_edges(), G2.number_of_nodes() + G2.number_of_edges()]
    domain = max(input_graph_sizes, default=G1.number_of_nodes() + G1.number_of_edges())
    
    return (mcs.number_of_nodes() + mcs.number_of_edges()) / domain


def edges_similarity(G1_dict, G2_dict):
    # Convert the dict representations to NetworkX graphs
    G1 = dictGraph_to_networkXGraph(G1_dict)
    G2 = dictGraph_to_networkXGraph(G2_dict)

    # Calculate common nodes
    common_nodes = set(G1.nodes()).intersection(set(G2.nodes()))
    all_nodes = set(G1.nodes()).union(set(G2.nodes()))
    total_unique_nodes = len(all_nodes)
    node_percentage = 100 * len(common_nodes) / total_unique_nodes if total_unique_nodes > 0 else 0

    # Calculate all possible edges and common edges
    all_possible_edges = {frozenset([u, v]) for u in all_nodes for v in all_nodes if u != v}
    edges_G1 = {frozenset(edge) for edge in G1.edges()}
    edges_G2 = {frozenset(edge) for edge in G2.edges()}

    # Count edges as matching if they are present in both or absent in both
    matching_edges = all_possible_edges - (edges_G1.symmetric_difference(edges_G2))
    edge_percentage = len(matching_edges) / len(all_possible_edges) if all_possible_edges else 0

    return node_percentage, edge_percentage


def approx_ged(G1_dict, G2_dict):
    # Convert the dict representations to NetworkX graphs
    G1 = dictGraph_to_networkXGraph(G1_dict)
    G2 = dictGraph_to_networkXGraph(G2_dict)

    ged = gm.GraphEditDistance(1,1,1,1) # all edit costs are equal to 1
    result = ged.compare([G1, G2], None)
    return min(result[0][1], result[1][0]) 