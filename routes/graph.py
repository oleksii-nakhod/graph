from flask import Blueprint, request, jsonify
from db.queries import get_node, list_nodes, create_node, create_node_batch, list_node_labels, update_node, delete_node, list_indexes, create_index, profile_function, get_edge, create_edge, create_edge_batch
from config import Config

graph_bp = Blueprint('graph', __name__)

@graph_bp.route('/api/nodes/<id>', methods=['GET'])
def api_get_node(id):
    node = get_node(id)
    if node is None:
        return jsonify({'message': 'Node not found'}), 404
    for field in Config.HIDDEN_FIELDS:
        if field in node:
            del node[field]
    return node


@graph_bp.route('/api/nodes', methods=['GET'])
def api_list_nodes():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    filters = {key: request.args[key] for key in request.args if key not in ['page', 'page_size']}
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    query = request.args.get('q', "")
    
    nodes = list_nodes(filters=filters, query=query, page=page, page_size=page_size, start_date=start_date, end_date=end_date)
    for node in nodes:
        for field in Config.HIDDEN_FIELDS:
            if field in node:
                del node[field]
    return jsonify({"results": nodes})


@graph_bp.route('/api/nodes', methods=['POST'])
def api_create_node():
    properties = request.json
    
    if 'labels' not in properties:
        return jsonify({'message': 'Label array is required'}), 400
    
    reserved_fields_used = set(properties.keys()).intersection(Config.RESERVED_FIELDS)
    if reserved_fields_used:
        return jsonify({'message': f'Reserved fields used: {reserved_fields_used}'}), 400

    reserved_labels_used = set(properties['labels']).intersection(Config.RESERVED_LABELS)
    if reserved_labels_used:
        return jsonify({'message': f'Reserved labels used: {reserved_labels_used}'}), 400
    
    node = create_node(properties)
    if node is None:
        return jsonify({'message': 'Node not created'}), 500
    return jsonify(node), 201


@graph_bp.route('/api/nodes/<node_id>', methods=['PUT'])
def api_update_node(node_id):
    properties = request.json
    labels = properties.get('labels', [])
    
    reserved_fields_used = set(properties.keys()).intersection(Config.RESERVED_FIELDS)
    if reserved_fields_used:
        return jsonify({'message': f'Reserved fields used: {reserved_fields_used}'}), 400
    
    reserved_labels_used = set(labels).intersection(Config.RESERVED_LABELS)
    if reserved_labels_used:
        return jsonify({'message': f'Reserved labels used: {reserved_labels_used}'}), 400
    
    node = update_node(node_id, properties)
    if node is None:
        return jsonify({'message': 'Node not found'}), 404
    return jsonify(node), 200


@graph_bp.route('/api/nodes/<node_id>', methods=['DELETE'])
def api_delete_node(node_id):
    node = delete_node(node_id)
    if node is None:
        return jsonify({'message': 'Node not found'}), 404
    return jsonify({'message': 'Node deleted successfully'}), 200


@graph_bp.route('/api/nodes/batch', methods=['POST'])
def api_create_node_batch():
    nodes = request.json
    
    if not isinstance(nodes, list):
        return jsonify({'message': 'A list of node data is required'}), 400
    
    for properties in nodes:
        if 'labels' not in properties:
            return jsonify({'message': 'Label array is required'}), 400
        
        reserved_fields_used = set(properties.keys()).intersection(Config.RESERVED_FIELDS)
        if reserved_fields_used:
            return jsonify({'message': f'Reserved fields used: {reserved_fields_used}'}), 400

        reserved_labels_used = set(properties['labels']).intersection(Config.RESERVED_LABELS)
        if reserved_labels_used:
            return jsonify({'message': f'Reserved labels used: {reserved_labels_used}'}), 400
    
    result = create_node_batch(nodes)
    if result is None:
        return jsonify({'message': 'Nodes not created'}), 500
    return jsonify(result), 201


@graph_bp.route('/api/edges/<id>', methods=['GET'])
def api_get_edge(id):
    edge = get_edge(id)
    if edge is None:
        return jsonify({'message': 'Edge not found'}), 404
    for field in Config.HIDDEN_FIELDS:
        if field in edge:
            del edge[field]
    return edge


@graph_bp.route('/api/edges', methods=['POST'])
def api_create_edge():
    data = request.json
    if 'src' not in data or 'dst' not in data:
        return jsonify({'message': 'Source and destination are required'}), 400
    reserved_fields_used = set(data.keys()).intersection(Config.RESERVED_FIELDS)
    if reserved_fields_used:
        return jsonify({'message': f'Reserved fields used: {reserved_fields_used}'}), 400
    edge = create_edge(data)
    if edge is None:
        return jsonify({'message': 'Edge not created'}), 500
    return jsonify(edge), 201


@graph_bp.route('/api/edges/batch', methods=['POST'])
def api_create_edge_batch():
    edges = request.json
    if not isinstance(edges, list):
        return jsonify({'message': 'A list of edge data is required'}), 400
    for data in edges:
        if 'src' not in data or 'dst' not in data:
            return jsonify({'message': 'Source and destination are required'}), 400
        reserved_fields_used = set(data.keys()).intersection(Config.RESERVED_FIELDS)
        if reserved_fields_used:
            return jsonify({'message': f'Reserved fields used: {reserved_fields_used}'}), 400
    result = create_edge_batch(edges)
    if result is None:
        return jsonify({'message': 'Edges not created'}), 500
    return jsonify(result), 201


@graph_bp.route('/api/labels', methods=['GET'])
def api_list_node_labels():
    labels = list_node_labels()
    return jsonify({"labels": labels})


@graph_bp.route('/api/indexes', methods=['POST'])
def api_create_index():
    data = request.json
    if 'label' not in data:
        return jsonify({'message': 'Label is required'}), 400
    index = create_index(data['label'])
    if index is None:
        return jsonify({'message': 'Index not created'}), 500
    return jsonify({'message': 'Index created successfully'}), 201
