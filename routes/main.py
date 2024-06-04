from flask import Blueprint, render_template, redirect, url_for, request, session, jsonify
from db.queries import list_nodes, get_node, list_node_labels, get_graph_neighborhood
from utils.helpers import create_openai_completion, create_openai_transcription
import json
from config import Config

main_bp = Blueprint('main', __name__)


@main_bp.route('/', methods=['GET'])
def index():
    recent_items = list_nodes()
    labels = list_node_labels()
    data = {
        'graph': get_graph_neighborhood([item['id'] for item in recent_items]),
        'labels': labels,
    }
    return render_template('index.html', data=data)


@main_bp.route('/search', methods=['GET'])
def search():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    query = request.args.get('q', '')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    insights = request.args.get('insights') == 'true'
    filters = request.args.get('filter', '{}')
    filters = json.loads(filters)
    
    labels = list_node_labels()
    nodes = list_nodes(filters=filters, query=query, page=page, page_size=page_size, start_date=start_date, end_date=end_date)
    for node in nodes:
        for field in Config.HIDDEN_FIELDS:
            if field in node:
                del node[field]
    
    data = {
        'results': nodes,
        'graph': get_graph_neighborhood([node['id'] for node in nodes]),
        'labels': labels,
    }
    return render_template('search.html', data=data, insights=insights)


@main_bp.route('/items/<item_id>', methods=['GET'])
def get_item(item_id):
    node = get_node(item_id)
    for field in Config.HIDDEN_FIELDS:
            if field in node:
                del node[field]
    if node is None:
        return redirect(url_for('main.index'))
    data = {
        'item': node,
        'labels': list_node_labels(),
        'graph': get_graph_neighborhood([item_id])
    }
    return render_template('get_item.html', data=data)


@main_bp.route('/new', methods=['GET'])
def create_item():
    if not 'logged_in' in session or not session['logged_in']:
        return redirect(url_for('main.index'))
    labels = list_node_labels()
    return render_template('create_item.html', data={"labels": labels})



@main_bp.route('/api/chat/completions', methods=['POST'])
def api_create_completion():
    messages = request.json.get('messages')
    return create_openai_completion(messages)


@main_bp.route('/api/audio/transcriptions', methods=['POST'])
def api_create_transcription():
    file = request.files.get('file')
    if not file:
        return jsonify({'message': 'File is required'}), 400
    allowed_formats = ['flac', 'm4a', 'mp3', 'mp4', 'mpeg', 'mpga', 'oga', 'ogg', 'wav', 'webm']
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in allowed_formats:
        return jsonify({'message': f"Unsupported file format. Supported formats: {allowed_formats}, got '{file_extension}'"}), 400
    text = create_openai_transcription(file)
    return jsonify({'text': text})