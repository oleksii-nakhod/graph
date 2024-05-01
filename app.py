from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, session
from waitress import serve
from flask_caching import Cache
import logging
import os
from dotenv import load_dotenv
import requests
import json
from openai import OpenAI
from datetime import datetime, timedelta
from neo4j import GraphDatabase
import bcrypt

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app.logger.info('Logging setup complete')

cache = Cache(
    app,
    config={
        'CACHE_TYPE': 'FileSystemCache',
        'CACHE_DIR': 'cache',
        'CACHE_DEFAULT_TIMEOUT': 86400
    }
)

openai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

URI = os.environ.get("NEO4J_URI")
AUTH = (os.environ.get("NEO4J_USERNAME"), os.environ.get("NEO4J_PASSWORD"))

class Neo4jConnection:
    
    def __init__(self, uri, auth):
        self.__uri = uri
        self.__auth = auth
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(self.__uri, auth=(self.__auth))
        except Exception as e:
            print("Failed to create the driver:", e)
        
    def close(self):
        if self.__driver is not None:
            self.__driver.close()
        
    def query(self, query, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try: 
            session = self.__driver.session(database=db) if db is not None else self.__driver.session() 
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed:", e)
        finally: 
            if session is not None:
                session.close()
        return response


def create_openai_embedding(input):
    response = openai_client.embeddings.create(
        input=input,
        model="text-embedding-3-small"
    )
    return response

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

def verify_password(input_password, hashed_password):
    if isinstance(input_password, str):
        input_password = input_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    print("input_password", input_password)
    print("hashed_password", hashed_password)
    return bcrypt.checkpw(input_password, hashed_password)



conn = Neo4jConnection(
    uri=URI, 
    auth=AUTH           
)

init_queries = {
    "create_vector_index_query": """
        CREATE VECTOR INDEX `document-embeddings` IF NOT EXISTS
        FOR (doc:Document)
        ON (doc.embedding)
        OPTIONS {indexConfig: {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'
        }}
    """,
    "create_anonymous_user_query": """
        CREATE USER anonymous IF NOT EXISTS SET PASSWORD 'password' CHANGE NOT REQUIRED
    """,
    "grant_read_access_query": """
        GRANT ROLE reader TO anonymous
    """
}

for query in init_queries.values():
    conn.query(query=query)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return redirect(url_for('index'))
    
    openai_response = create_openai_embedding(query)
    
    neo4j_query = """
        CALL db.index.vector.queryNodes('document-embeddings', $num_results, $embedding) YIELD node AS similarDocument, score
        RETURN elementId(similarDocument) AS nodeId,similarDocument.title AS title, similarDocument.content AS content, score
    """
    results = conn.query(
        query=neo4j_query,
        parameters={
            'embedding': openai_response.data[0].embedding,
            'num_results': 5
        },
        db="neo4j"
    )
    return render_template('search.html', results=results)


@app.route('/create', methods=['POST'])
def create_document():
    if not 'logged_in' in session or not session['logged_in']:
        return jsonify({'error': 'You do not have permission to create documents'}), 403
    
    data = request.json

    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'error': 'Title and content are required'}), 400

    title = data['title']
    content = data['content']
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    response = create_openai_embedding(f"{title} {content}")

    query = """
        CREATE (a:Document {title: $title, content: $content, embedding: $embedding, created_at: $created_at})
        RETURN a
    """
    conn.query(
        query=query,
        parameters={'title': title, 'content': content, 'embedding': response.data[0].embedding, 'created_at': created_at},
        db="neo4j"
    )
    
    return jsonify({'message': 'Document created successfully'}), 201


@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    existing_user_query = """
        MATCH (u:User {username: $username})
        RETURN elementId(u) AS id, u.username AS username, u.password AS password
    """
    existing_user = conn.query(
        query=existing_user_query,
        parameters={'username': username},
        db="neo4j"
    )
    if not existing_user:
        return jsonify({'error': 'User not found'}), 404
    
    hashed_password = existing_user[0][2]
    if not verify_password(password, hashed_password):
        return jsonify({'error': 'Incorrect password'}), 401

    session['logged_in'] = True
    session['id'] = existing_user[0][0]
    session['username'] = existing_user[0][1]
    return jsonify({'message': 'Login successful'}), 200

@app.route('/signup', methods=['POST'])
def signup():
    username = request.json.get('username')
    password = request.json.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    existing_user_query = """
        MATCH (u:User {username: $username})
        RETURN count(u) > 0 AS exists
    """
    existing_user = conn.query(
        query=existing_user_query,
        parameters={'username': username},
        db="neo4j"
    )[0][0]
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 409
    
    hashed_password = hash_password(password)
    print(hashed_password)
    query = """
        CREATE (u:User {username: $username, password: $password})
        RETURN elementId(u) AS id, u.username AS username
    """
    user = conn.query(
        query=query,
        parameters={
            'username': username,
            'password': hashed_password.decode('utf-8')
        },
        db="neo4j"
    )
    session['logged_in'] = True
    session['id'] = user[0][0]
    session['username'] = user[0][1]
    return jsonify({'message': 'Signup successful'}), 201


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))

    
def check_cache(cache_key):
    cached_data = cache.get(cache_key)
    if cached_data:
        app.logger.info(f'{cache_key} cache hit! Returning cached data.')
        return cached_data
    else:
        app.logger.info(f'{cache_key} cache miss! Making a new request...')
        return None


@app.errorhandler(404)
def handle_404(e):
    return redirect(url_for('index'))


@app.errorhandler(500)
def handle_500(e):
    return redirect(url_for('index'))


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5004)