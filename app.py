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
import itertools
from bs4 import BeautifulSoup

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

URI = os.environ.get("NEO4J_URI")
ADMIN_AUTH = (os.environ.get("NEO4J_ADMIN_USERNAME"), os.environ.get("NEO4J_ADMIN_PASSWORD"))
READER_AUTH = (os.environ.get("NEO4J_READER_USERNAME"), os.environ.get("NEO4J_READER_PASSWORD"))
conn = Neo4jConnection(
    uri=URI, 
    auth=ADMIN_AUTH           
)

def create_openai_embedding(input):
    response = openai_client.embeddings.create(
        input=input,
        model="text-embedding-3-small"
    )
    return response

def html_to_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

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


def convert_results_to_nodes_and_links(results):
    nodes = [{'id': result['id'], 'title': result['title'], 'content': result['content'], 'score': result['score']} for result in results]
    links = []
    for combination in itertools.combinations(nodes, 2):
        links.append({'source': combination[0]['id'], 'target': combination[1]['id']})
    return nodes, links


def init_database():
    


    init_queries = {
        "create_vector_index_query": """
            CREATE VECTOR INDEX `document-embeddings` IF NOT EXISTS
            FOR (doc:Document)
            ON (doc.embedding)
            OPTIONS {indexConfig: {
                `vector.dimensions`: 1536,
                `vector.similarity_function`: 'cosine'
            }}
        """
    }

    for query in init_queries.values():
        conn.query(query=query)


init_database()


@app.route('/', methods=['GET'])
def index():
    query = """
    MATCH (u:User)-[r:CREATED]->(d:Document)
    RETURN u.username AS user_name, elementId(u) AS user_id,
           COLLECT({doc_id: elementId(d), doc_title: d.title, doc_content: d.content, rel_type: type(r)}) AS documents
    """
    results = conn.query(query=query, db="neo4j")

    nodes = []
    links = []
    result_data = []

    node_ids = set()

    for result in results:
        if result['user_id'] not in node_ids:
            nodes.append({"title": result['user_name'], "id": result['user_id'], "label": "User"})
            node_ids.add(result['user_id'])

        for doc in result['documents']:
            if doc['doc_id'] not in node_ids:
                nodes.append({"title": doc['doc_title'], "id": doc['doc_id'], "label": "Document"})
                node_ids.add(doc['doc_id'])
            links.append({"source": doc['doc_id'], "target": result['user_id']})
            result_data.append({
                "title": doc['doc_title'],
                "id": doc['doc_id'],
                "content": doc['doc_content'],
                "score": 1
            })

    response_data = {
        "graph": {
            "nodes": nodes,
            "links": links
        },
        "results": result_data
    }

    return render_template('index.html', data=response_data)


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    if not query:
        return redirect(url_for('index'))
    
    openai_response = create_openai_embedding(query)
    
    neo4j_query = """
        CALL db.index.vector.queryNodes('document-embeddings', $num_results, $embedding) YIELD node AS similarDocument, score
        RETURN elementId(similarDocument) AS id, similarDocument.title AS title, similarDocument.content AS content, score
    """
    results = conn.query(
        query=neo4j_query,
        parameters={
            'embedding': openai_response.data[0].embedding,
            'num_results': 5
        },
        db="neo4j"
    )
    nodes, links = convert_results_to_nodes_and_links(results)
    
    
    return render_template('search.html', nodes=nodes, links=links)



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
    
    response = create_openai_embedding(f"{title} {html_to_text(content)}")

    query = """
        MATCH (u:User) WHERE elementId(u) = $user_id
        CREATE (a:Document {title: $title, content: $content, embedding: $embedding, created_at: $created_at})
        CREATE (u)-[:CREATED]->(a)
        RETURN a
    """
    conn.query(
        query=query,
        parameters={
            'user_id': session['id'],
            'title': title,
            'content': content,
            'embedding': response.data[0].embedding,
            'created_at': created_at
        },
        db="neo4j"
    )
    
    return jsonify({'message': 'Document created successfully'}), 201


@app.route('/new', methods=['GET'])
def new():
    if not 'logged_in' in session or not session['logged_in']:
        return redirect(url_for('index'))
    
    return render_template('new.html')


@app.route('/docs/<document_id>', methods=['GET'])
def view_document(document_id):
    query = """
        MATCH (d:Document)
        WHERE elementId(d) = $document_id
        RETURN d.title AS title, d.content AS content
    """
    results = conn.query(query=query, parameters={'document_id': document_id}, db="neo4j")
    if not results:
        return redirect(url_for('index'))
    
    return render_template('docs.html', title=results[0]['title'], content=results[0]['content'])


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