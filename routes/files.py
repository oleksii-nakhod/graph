from flask import Blueprint, request, jsonify, session, send_from_directory
from werkzeug.utils import secure_filename
import os
import uuid

files_bp = Blueprint('files', __name__)

FILE_DIR = 'static/files'
if not os.path.exists(FILE_DIR):
    os.makedirs(FILE_DIR)

@files_bp.route('/api/files/<file_id>', methods=['GET'])
def api_get_file(file_id):
    file_path = os.path.join(FILE_DIR, file_id)
    if not os.path.exists(file_path):
        return jsonify({'message': 'File not found'}), 404
    return send_from_directory(FILE_DIR, file_id, as_attachment=True)

@files_bp.route('/api/files', methods=['POST'])
def api_create_file():
    if not 'logged_in' in session or not session['logged_in']:
        return jsonify({'message': 'You do not have permission to upload files'}), 403
    
    file = request.files.get('file')
    if not file:
        return jsonify({'message': 'File is required'}), 400
    
    original_filename = secure_filename(file.filename)
    filename_base, file_extension = os.path.splitext(original_filename)

    random_uuid = uuid.uuid4().hex
    new_filename = f"{filename_base}_{random_uuid}{file_extension}"
    
    file_path = os.path.join(FILE_DIR, new_filename)
    file.save(file_path)
    
    return jsonify({'id': new_filename}), 201

@files_bp.route('/api/files/<file_id>', methods=['DELETE'])
def api_delete_file(file_id):
    if not 'logged_in' in session or not session['logged_in']:
        return jsonify({'message': 'You do not have permission to delete files'}), 403
    
    file_path = os.path.join(FILE_DIR, file_id)
    if not os.path.exists(file_path):
        return jsonify({'message': 'File not found'}), 404
    
    os.remove(file_path)
    return jsonify({'message': 'File deleted successfully'}), 200
