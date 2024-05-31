from flask import Blueprint, render_template, redirect, url_for, request, session, jsonify
from db.queries import get_recent_documents, search_documents, get_document_by_id, create_document, update_document, delete_document
from utils.helpers import create_openai_embedding, html_to_text, convert_results, get_documents_data, create_openai_completion, create_openai_transcription
from datetime import datetime, timezone

main_bp = Blueprint('main', __name__)


@main_bp.route('/', methods=['GET'])
def index():
    results = get_recent_documents()
    response_data = convert_results(results)
    return render_template('index.html', data=response_data)


@main_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return redirect(url_for('index'))
    
    openai_response = create_openai_embedding(query)
    results = search_documents(openai_response.data[0].embedding, 5)
    data = convert_results(results)
    return render_template('search.html', data=data)


@main_bp.route('/api/docs/<document_id>', methods=['GET'])
def api_get_document(document_id):
    document = get_document_by_id(document_id)
    if document is None:
        return jsonify({'message': 'Document not found'}), 404
    return jsonify(document)


@main_bp.route('/api/docs', methods=['GET'])
def api_list_documents():
    query = request.args.get('q')
    data = get_documents_data(query)
    if data is None:
        return jsonify({'message': 'No data found'}), 404
    return jsonify(data)


@main_bp.route('/api/docs', methods=['POST'])
def api_create_document():
    if not 'logged_in' in session or not session['logged_in']:
        return jsonify({'message': 'You do not have permission to create documents'}), 403
    
    data = request.json
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'message': 'Title and content are required'}), 400

    title = data['title']
    content = data['content']
    created_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    response = create_openai_embedding(f"{title} {html_to_text(content)}")
    
    result = create_document(session['id'], title, content, response.data[0].embedding, created_at)
    return jsonify({'id': result[0]['id']}), 201


@main_bp.route('/api/docs/<document_id>', methods=['PUT'])
def api_update_document(document_id):
    if not 'logged_in' in session or not session['logged_in']:
        return jsonify({'message': 'You do not have permission to update documents'}), 403
    
    data = request.json
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'message': 'Title and content are required'}), 400
    
    title = data['title']
    content = data['content']
    response = create_openai_embedding(f"{title} {html_to_text(content)}")
    
    result = update_document(document_id, title, content, response.data[0].embedding)
    if not result:
        return jsonify({'message': 'Document not found'}), 404
    
    return jsonify({'message': 'Document updated successfully'}), 200


@main_bp.route('/api/docs/<document_id>', methods=['DELETE'])
def api_delete_document(document_id):
    if not 'logged_in' in session or not session['logged_in']:
        return jsonify({'message': 'You do not have permission to delete documents'}), 403
    
    result = delete_document(document_id)
    if not result:
        return jsonify({'message': 'Document not found'}), 404
    
    return jsonify({'message': 'Document deleted successfully'}), 200


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
    return jsonify({text})