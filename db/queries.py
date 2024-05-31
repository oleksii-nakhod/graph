from models.neo4j_connection import conn
from utils.helpers import generate_id

reserved_properties = ['id', 'created_at', 'updated_at']

def create_vector_index():
    query = """
        CREATE VECTOR INDEX `document-embeddings` IF NOT EXISTS
        FOR (doc:Document)
        ON (doc.embedding)
        OPTIONS {indexConfig: {
            `vector.dimensions`: 1536,
            `vector.similarity_function`: 'cosine'
        }}
    """
    conn.query(query=query)

def get_recent_documents():
    query = """
    MATCH (u:User)-[r:CREATED]->(d:Document)
    WITH u.username AS user_name, elementId(u) AS user_id, d, r
    ORDER BY d.created_at DESC
    LIMIT 6
    RETURN user_name, user_id,
        COLLECT({
            id: elementId(d),
            title: d.title,
            content: d.content,
            created_at: d.created_at,
            author: user_name,
            rel_type: type(r)
        }) AS documents
    """
    return conn.query(query=query, db="neo4j")

def search_documents(embedding, num_results):
    query = """
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
    return conn.query(
        query=query,
        parameters={
            'embedding': embedding,
            'num_results': num_results
        },
        db="neo4j"
    )

def get_document_by_id(document_id):
    query = """
        MATCH (u:User)-[:CREATED]->(d:Document)
        WHERE elementId(d) = $document_id
        RETURN elementId(d) AS id, d.title AS title, d.content AS content, d.created_at AS created_at, u.username AS created_by
    """
    return conn.query(query=query, parameters={'document_id': document_id}, db="neo4j")

def create_document(user_id, title, content, embedding, created_at):
    query = """
        MATCH (u:User) WHERE elementId(u) = $user_id
        CREATE (a:Document {title: $title, content: $content, embedding: $embedding, created_at: $created_at})
        CREATE (u)-[:CREATED]->(a)
        RETURN elementId(a) AS id
    """
    return conn.query(
        query=query,
        parameters={
            'user_id': user_id,
            'title': title,
            'content': content,
            'embedding': embedding,
            'created_at': created_at
        },
        db="neo4j"
    )

def update_document(document_id, title, content, embedding):
    query = """
        MATCH (a:Document) WHERE elementId(a) = $document_id
        SET a.title = $title, a.content = $content, a.embedding = $embedding
        RETURN a
    """
    return conn.query(
        query=query,
        parameters={
            'document_id': document_id,
            'title': title,
            'content': content,
            'embedding': embedding
        },
        db="neo4j"
    )

def delete_document(document_id):
    query = """
        MATCH (a:Document) WHERE elementId(a) = $document_id
        WITH a
        DETACH DELETE a
        RETURN a
    """
    return conn.query(
        query=query,
        parameters={'document_id': document_id},
        db="neo4j"
    )

def get_user_by_username(username):
    query = """
        MATCH (u:User {username: $username})
        RETURN elementId(u) AS id, u.username AS username, u.password AS password
    """
    return conn.query(
        query=query,
        parameters={'username': username},
        db="neo4j"
    )

def create_user(username, hashed_password):
    query = """
        CREATE (u:User {username: $username, password: $password})
        RETURN elementId(u) AS id, u.username AS username
    """
    return conn.query(
        query=query,
        parameters={
            'username': username,
            'password': hashed_password
        },
        db="neo4j"
    )

def user_exists(username):
    query = """
        MATCH (u:User {username: $username})
        RETURN count(u) > 0 AS exists
    """
    return conn.query(
        query=query,
        parameters={'username': username},
        db="neo4j"
    )[0]['exists']

def get_node(id):
    query = """
        MATCH (n) WHERE n.id = $id
        RETURN properties(n) AS node, labels(n) AS labels
    """
    records = conn.query(
        query=query,
        parameters={'id': id},
        db="neo4j"
    )
    if records:
        node = records[0]['node']
        node['labels'] = records[0]['labels']
        return node
    else:
        return None


def list_nodes(filters=None, page=1, page_size=10):
    skip = (page - 1) * page_size
    
    label = filters.pop('label', None) if filters else None
    
    where_clause = ""
    if filters:
        filter_conditions = []
        for key, value in filters.items():
            filter_conditions.append(f"n.{key} = ${key}")
        where_clause = "WHERE " + " AND ".join(filter_conditions)
    
    label_clause = f":{label}" if label else ""
    
    query = f"""
        MATCH (n{label_clause})
        {where_clause}
        RETURN properties(n) AS node, labels(n) AS labels
        SKIP $skip LIMIT $limit
    """
    
    parameters = filters if filters else {}
    parameters.update({"skip": skip, "limit": page_size})
    
    records = conn.query(
        query=query,
        parameters=parameters,
        db="neo4j"
    )
    
    results = []
    for record in records:
        node = record['node']
        node['labels'] = record['labels']
        results.append(node)
    
    return results


def create_node(properties):
    labels = properties.pop('labels', None)
    slug = properties.pop('slug', None)
    
    for key in reserved_properties:
        properties.pop(key, None)
        
    properties['id'] = generate_id(labels=labels, slug=slug)
    
    query = f"""
        CREATE (n:{':'.join(labels)} $properties)
        RETURN n.id AS id
    """
    
    records = conn.query(
        query=query,
        parameters={'properties': properties},
        db="neo4j"
    )
    
    if records:
        return {
            'id': records[0]['id']
        }
    else:
        return None
    

def create_graph_batch(batch):
    for item in batch:
        labels = ":".join(item.pop('labels', []))
        edges = item.pop('edges', [])
        for edge in edges:
            cypher_query = f'''
            MERGE (a:{labels} {{id: $item_id}})
            SET a.features = $features, a.label = $label
            MERGE (b {{id: $dst_id}})
            MERGE (a)-[r:{edge['type']}]->(b)
            '''
            conn.query(query=cypher_query, parameters={
                'item_id': item['id'],
                'features': item['features'],
                'label': item['label'],
                'dst_id': edge['dst_id']
            }, db="neo4j")



def create_nodes_in_batches(data):
    batch_size = 1000
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        create_graph_batch(batch)