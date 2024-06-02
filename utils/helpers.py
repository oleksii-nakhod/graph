from bs4 import BeautifulSoup
from openai import OpenAI
from config import Config
from io import BytesIO
from models.neo4j_connection import conn
import shortuuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask_caching import Cache
from openai_tools import tools, tool_names, functions
import json
from flask import stream_with_context

openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

cache = Cache()
def init_cache(app):
    cache.init_app(app, config={
        'CACHE_TYPE': 'FileSystemCache',
        'CACHE_DIR': 'cache',
        'CACHE_DEFAULT_TIMEOUT': 86400
    })


def check_cache(cache_key):
    return cache.get(cache_key)


def create_openai_embedding(input):
    cache_key = f'openai_embedding_{input}'
    cached_data = check_cache(cache_key)
    if cached_data:
        return cached_data
    embedding = openai_client.embeddings.create(
        input=input,
        model=Config.OPENAI_EMBEDDING_MODEL
    ).data[0].embedding
    cache.set(cache_key, embedding)
    return embedding


def create_item_embedding(item):
    return create_openai_embedding(f"Title: {item['title']}\nLabels: {', '.join(item['labels'])}\nContent: {item['content']}")


def create_openai_completion(messages):
    def generate():
        stream = openai_client.chat.completions.create(
            model=Config.OPENAI_COMPLETION_MODEL,
            messages=messages,
            tools=tools,
            tool_choice='auto',
            stream=True
        )
        streaming_content = ""
        tool_calls = []
        for chunk in stream:
            msg = chunk.choices[0]
            delta = msg.delta
            if delta.content is not None:
                streaming_content += delta.content
                yield delta.content
            if delta.tool_calls is not None:
                tc_chunks = delta.tool_calls
                for tc_chunk in tc_chunks:
                    if len(tool_calls) <= tc_chunk.index:
                        tool_calls.append({"id": "", "type": "function", "function": { "name": "", "arguments": "" } })
                    tc = tool_calls[tc_chunk.index]
                    
                    if tc_chunk.id:
                        tc["id"] += tc_chunk.id
                    if tc_chunk.function.name:
                        tc["function"]["name"] += tc_chunk.function.name
                    if tc_chunk.function.arguments:
                        tc["function"]["arguments"] += tc_chunk.function.arguments
            if msg.finish_reason == "stop":
                messages.append({"role": "assistant", "content": streaming_content})
            elif msg.finish_reason == "tool_calls":
                messages.append(
                    {
                        "tool_calls": tool_calls,
                        "role": "assistant",
                        "content": None
                    }
                )
                for tool_call in tool_calls:
                    before_tool_call = f"<div class='alert alert-primary' role='alert'>Triggered  <span class='fw-bold'>{tool_call['function']['name']}</span> with arguments {tool_call['function']['arguments']}</div>"
                    yield before_tool_call
                    function_output = json.dumps(use_tool(
                        tool_call["function"]["name"], json.loads(tool_call["function"]["arguments"])
                    ))
                    messages.append(
                        {
                            "tool_call_id": tool_call["id"],
                            "role": "tool",
                            "content": f"{function_output}"
                        }
                    )
                yield from create_openai_completion(
                    messages
                )
    
    return stream_with_context(generate())


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
    return generate_password_hash(password)


def verify_password(hashed_password, input_password):
    return check_password_hash(hashed_password, input_password)


def convert_results(results):
    nodes = []
    links = []
    result_data = []

    node_ids = set()

    for result in results:
        if result['user_id'] not in node_ids:
            nodes.append({"title": result['user_name'], "id": result['user_id'], "label": "User"})
            node_ids.add(result['user_id'])

        for doc in result['items']:
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


def list_tools():
    return tools


def use_tool(tool_name, tool_arguments):
    if tool_name in tool_names:
        tool = functions[tool_name]
        return tool(**tool_arguments)
    else:
        return {"error": "Tool not found"}