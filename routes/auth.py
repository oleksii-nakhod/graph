from flask import Blueprint, request, jsonify, session
from db.queries import get_user_by_username, create_user, user_exists
from utils.helpers import hash_password, verify_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400
    
    user = get_user_by_username(username)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    hashed_password = user[0]['password']
    if not verify_password(password, hashed_password):
        return jsonify({'message': 'Incorrect password'}), 401

    session['logged_in'] = True
    session['id'] = user[0]['id']
    session['username'] = user[0]['username']
    return jsonify({'message': 'Login successful'}), 200

@auth_bp.route('/api/signup', methods=['POST'])
def api_signup():
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400
    
    if user_exists(username):
        return jsonify({'message': 'Username already exists'}), 409
    
    hashed_password = hash_password(password).decode('utf-8')
    user = create_user(username, hashed_password)
    session['logged_in'] = True
    session['id'] = user[0]['id']
    session['username'] = user[0]['username']
    return jsonify({'message': 'Signup successful'}), 201

@auth_bp.route('/api/logout', methods=['POST'])
def api_logout():
    if not 'logged_in' in session or not session['logged_in']:
        return jsonify({'message': 'You are not logged in'}), 401
    session.clear()
    return jsonify({'message': 'Logout successful'}), 200
