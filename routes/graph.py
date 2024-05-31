from flask import Blueprint, request, jsonify
from models.neo4j_connection import conn
from utils.helpers import create_openai_embedding
from db.queries import get_node, list_nodes, create_node, create_nodes_in_batches

graph_bp = Blueprint('graph', __name__)


@graph_bp.route('/api/nodes/<id>', methods=['GET'])
def api_get_node(id):
    node = get_node(id)
    if node is None:
        return jsonify({'message': 'Node not found'}), 404
    return node


@graph_bp.route('/api/nodes', methods=['GET'])
def api_list_nodes():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    
    filters = {key: request.args[key] for key in request.args if key not in ['page', 'page_size']}
    
    nodes = list_nodes(filters, page, page_size)
    return jsonify(nodes)


@graph_bp.route('/api/nodes', methods=['POST'])
def api_create_node():
    properties = request.json
    if not properties.get('labels'):
        return jsonify({'message': 'Label array is required'}), 400
    node = create_node(properties)
    return jsonify(node), 201


@graph_bp.route('/api/nodes/batch', methods=['POST'])
def api_create_nodes_batch():
    data = request.json
    if not isinstance(data, list) or not data:
        return jsonify({'message': 'A list of node data is required'}), 400
    create_nodes_in_batches(data)
    return jsonify({'message': 'Nodes and edges created successfully'}), 201



@graph_bp.route('/api/edges', methods=['POST'])
def api_create_edge():
    pass
