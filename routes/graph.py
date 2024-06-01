from flask import Blueprint, request, jsonify
from models.neo4j_connection import conn
from utils.helpers import create_openai_embedding
from db.queries import get_node, list_nodes, create_node, create_nodes_in_batches, list_node_labels, update_node, delete_node, list_indexes, create_index

graph_bp = Blueprint('graph', __name__)

reserved_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'username', 'password', 'embedding']
hidden_fields = ['password']
reserved_labels = ['User']


@graph_bp.route('/api/nodes/<id>', methods=['GET'])
def api_get_node(id):
    node = get_node(id)
    for field in hidden_fields:
        if field in node:
            del node[field]
    if node is None:
        return jsonify({'message': 'Node not found'}), 404
    return node


@graph_bp.route('/api/nodes', methods=['GET'])
def api_list_nodes():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    filters = {key: request.args[key] for key in request.args if key not in ['page', 'page_size']}
    query = request.args.get('q', "")
    
    nodes = list_nodes(filters=filters, query=query, page=page, page_size=page_size)
    for node in nodes:
        for field in hidden_fields:
            if field in node:
                del node[field]
    return jsonify({"results": nodes})


@graph_bp.route('/api/nodes', methods=['POST'])
def api_create_node():
    properties = request.json
    
    if 'labels' not in properties:
        return jsonify({'message': 'Label array is required'}), 400
    
    reserved_fields_used = set(properties.keys()).intersection(reserved_fields)
    if reserved_fields_used:
        return jsonify({'message': f'Reserved fields used: {reserved_fields_used}'}), 400

    reserved_labels_used = set(properties['labels']).intersection(reserved_labels)
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
    
    reserved_fields_used = set(properties.keys()).intersection(reserved_fields)
    if reserved_fields_used:
        return jsonify({'message': f'Reserved fields used: {reserved_fields_used}'}), 400
    
    reserved_labels_used = set(labels).intersection(reserved_labels)
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
def api_create_nodes_batch():
    data = request.json
    if not isinstance(data, list) or not data:
        return jsonify({'message': 'A list of node data is required'}), 400
    create_nodes_in_batches(data)
    return jsonify({'message': 'Nodes and edges created successfully'}), 201


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
