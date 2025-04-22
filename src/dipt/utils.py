def nested_dict_to_edges(nested_dict, parent=None):
    edges = []
    for node, children in nested_dict.items():
        if parent is not None:  # Root has no parent → skip
            edges.append((parent, node))  # Add edge (parent → child)
        if isinstance(children, dict):  # Recurse into children
            edges.extend(nested_dict_to_edges(children, parent=node))
    return edges


def rename_nodes_to_ids(edges):
    # Get all unique nodes and assign IDs
    unique_nodes = set()
    for parent, child in edges:
        unique_nodes.update([parent, child])
    node_to_id = {node: i for i, node in enumerate(sorted(unique_nodes))}  # Sort for consistency

    # Replace names with IDs in edges
    id_edges = [(node_to_id[parent], node_to_id[child]) for parent, child in edges]
    id_to_node = {node_to_id[key]: key for key in node_to_id}
    return id_edges, id_to_node  # Return edges and mapping
