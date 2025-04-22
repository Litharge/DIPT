def nested_dict_to_edges(nested_dict, parent=None):
    "returns breadth-first edges of tree"
    edges = []
    for node, children in nested_dict.items():
        if parent is not None:  # Root has no parent → skip
            edges.append((parent, node))  # Add edge (parent → child)
        if isinstance(children, dict):  # Recurse into children
            edges.extend(nested_dict_to_edges(children, parent=node))
    return edges


def rename_nodes_to_ids(nested_dict, edges):
    """Given breadth first edges, rename the nodes with breadth first numbers and return the mapping used"""
    unique_nodes = []
    # Add the root node
    unique_nodes.append(list(nested_dict.keys())[0])
    # Get all the unique nodes that are not root
    for parent, child in edges:
        if child not in unique_nodes:
            unique_nodes.append(child)
    node_to_id = {node: i for i, node in enumerate(unique_nodes)}  # Sort for consistency

    # Replace names with IDs in edges
    print("line 19")
    print(edges)
    print(node_to_id)
    id_edges = [(node_to_id[parent], node_to_id[child]) for parent, child in edges]
    id_to_node = {node_to_id[key]: key for key in node_to_id}
    return id_edges, id_to_node, node_to_id  # Return edges and mapping
