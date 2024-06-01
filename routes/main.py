from flask import Blueprint, render_template, redirect, url_for, request, session, jsonify
from db.queries import list_nodes, get_node, list_node_labels, get_graph_neighborhood
from utils.helpers import create_openai_embedding, html_to_text, convert_results, create_openai_completion, create_openai_transcription
from datetime import datetime, timezone

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
    
    filters = {key: request.args[key] for key in request.args if key not in ['page', 'page_size']}
    
    data = {
        "results": list_nodes(filters, page, page_size)
    }
    print(data)
    return render_template('search.html', data=data)


@main_bp.route('/ask', methods=['GET'])
def ask():
    query = request.args.get('q')
    if not query:
        return redirect(url_for('main.index'))
    
    openai_response = create_openai_embedding(query)
    results = list_nodes(openai_response.data[0].embedding, 5)
    data = convert_results(results)
    return render_template('ask.html', data=data)


@main_bp.route('/items/<item_id>', methods=['GET'])
def get_item(item_id):
    item = get_node(item_id)
    if item is None:
        return redirect(url_for('main.index'))
    return render_template('get_item.html', data=item)


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