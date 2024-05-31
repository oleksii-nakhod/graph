import bcrypt
from bs4 import BeautifulSoup
from openai import OpenAI
from config import Config
from io import BytesIO
from models.neo4j_connection import conn
import shortuuid

openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

def create_openai_embedding(input):
    response = openai_client.embeddings.create(
        input=input,
        model=Config.OPENAI_EMBEDDING_MODEL
    )
    return response

def create_openai_completion(messages):
    def generate():
        stream = openai_client.chat.completions.create(
            model=Config.OPENAI_COMPLETION_MODEL,
            messages=messages,
            stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    return generate(), {"Content-Type": "text/plain"}


def create_openai_transcription(file):
    buffer = BytesIO(file.read())
    buffer.name = file.filename
    transcript = openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=buffer
    )
    return transcript.text


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
    return bcrypt.checkpw(input_password, hashed_password)


def convert_results(results):
    nodes = []
    links = []
    result_data = []

    node_ids = set()

    for result in results:
        if result['user_id'] not in node_ids:
            nodes.append({"title": result['user_name'], "id": result['user_id'], "label": "User"})
            node_ids.add(result['user_id'])

        for doc in result['documents']:
            if doc['id'] not in node_ids:
                nodes.append({"title": doc['title'], "id": doc['id'], "label": "Document"})
                node_ids.add(doc['id'])
            links.append({"source": doc['id'], "target": result['user_id']})
            result_data.append({
                "title": doc['title'],
                "id": doc['id'],
                "content": doc['content'],
                "created_at": doc['created_at'],
                "author": doc['author'],
                "score": doc.get('score', 1),
            })

    data = {
        "graph": {
            "nodes": nodes,
            "links": links
        },
        "results": result_data
    }
    
    return data


def get_documents_data(query):
    if not query:
        return None
    
    openai_response = create_openai_embedding(query)
    
    neo4j_query = """
        CALL db.index.vector.queryNodes('document-embeddings', $num_results, $embedding) YIELD node AS similarDocument, score
        MATCH (u:User)-[r:CREATED]->(d:Document)
        WHERE d = similarDocument
        WITH u, d, r, score
        ORDER BY score DESC
        WITH u, COLLECT({
            id: elementId(d), 
            title: d.title, 
            content: d.content,
            created_at: d.created_at, 
            author: u.username,
            rel_type: type(r), 
            score: score
        }) AS documents
        RETURN u.username AS user_name, elementId(u) AS user_id, documents
    """
    
    results = conn.query(
        query=neo4j_query,
        parameters={
            'embedding': openai_response.data[0].embedding,
            'num_results': 5
        },
        db="neo4j"
    )
    data = convert_results(results)
    data['query'] = query
    return data


def generate_id(labels, slug, length=16):
    slug = slug or labels[0][:3].lower()
    return f"{slug}_{shortuuid.ShortUUID().random(length)}"