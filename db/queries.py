from models.neo4j_connection import conn
from utils.helpers import generate_id, create_openai_embedding
from datetime import datetime, timezone
from config import Config


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


def list_nodes(filters=None, query="", page=1, page_size=10, sort_by='created_at', sort_order='DESC'):
    skip = (page - 1) * page_size
    label = filters.pop('label', None) if filters else None
    where_clause = ""
    if filters:
        filter_conditions = []
        for key, value in filters.items():
            filter_conditions.append(f"n.{key} = ${key}")
        where_clause = "WHERE " + " AND ".join(filter_conditions)
    
    label_clause = f":{label}" if label else ""
    
    
    neo4j_query = f"""
        MATCH (n {label_clause})
        {where_clause}
        WITH n

        CALL db.index.vector.queryNodes('item_embedding_index', {page * page_size * 2}, $embedding) 
        YIELD node AS similarDocument, score
        WITH DISTINCT similarDocument, score, properties(similarDocument) AS nodeProperties, labels(similarDocument) AS nodeLabels

        ORDER BY score DESC, similarDocument.{sort_by} {sort_order}
        WITH DISTINCT similarDocument, nodeProperties, nodeLabels, score

        WITH collect({{nodeProperties: nodeProperties, nodeLabels: nodeLabels, score: score}}) AS results
        UNWIND results[..{page_size}] AS result
        RETURN result.nodeProperties, result.nodeLabels, result.score
    """
    
    parameters = filters if filters else {}
    parameters['embedding'] = create_openai_embedding(query)
    
    records = conn.query(
        query=neo4j_query,
        parameters=parameters,
        db="neo4j"
    )
    results = []
    for record in records:
        node = record['nodeProperties']
        node['labels'] = record['nodeLabels']
        node['score'] = record['score']
        node.pop('embedding', None)
        
        results.append(node)
    
    return results


def create_node(properties):
    labels = properties.pop('labels', [])
    slug = properties.pop('slug', None)
    title = properties.pop('title', None)
    content = properties.pop('content', None)
    
    properties['id'] = generate_id(labels=labels, slug=slug)
    
    properties['title'] = title
    properties['content'] = content
    time_now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    properties['created_at'] = time_now
    properties['updated_at'] = time_now
    properties['embedding'] = create_openai_embedding(f"{title} {content}")
    
    labels.append('Item')
    
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


def update_node(id, properties):
    labels = properties.pop('labels', [])
    label_clause = f", n:{':'.join(labels)}" if labels else ""
    title = properties.pop('title', None)
    content = properties.pop('content', None)
    
    properties['title'] = title
    properties['content'] = content
    time_now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    properties['updated_at'] = time_now
    properties['embedding'] = create_openai_embedding(f"{title} {content}")
    
    query = f"""
        MATCH (n) WHERE n.id = $id
        SET n += $properties{label_clause}
        RETURN n.id AS id
    """
    
    records = conn.query(
        query=query,
        parameters={'id': id, 'properties': properties},
        db="neo4j"
    )
    
    if records:
        return {
            'id': records[0]['id']
        }
    else:
        return None


def delete_node(id):
    query = """
        MATCH (n) WHERE n.id = $id
        DETACH DELETE n
        RETURN n
    """
    result = conn.query(
        query=query,
        parameters={'id': id},
        db="neo4j"
    )
    return result if result else None
    

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


def list_node_labels():
    query = """
        CALL db.labels()
    """
    records = conn.query(
        query=query,
        db="neo4j"
    )
    return [record['label'] for record in records]


def get_graph_neighborhood(ids):
    query = f"""
        WITH {ids} AS nodeIds
        MATCH (n)
        WHERE n.id IN nodeIds
        OPTIONAL MATCH (n)-[r]->(m)
        WITH COLLECT(DISTINCT n) + COLLECT(DISTINCT m) AS allNodes, COLLECT(DISTINCT r) AS allRels
        RETURN {{
            nodes: [node IN allNodes WHERE node IS NOT NULL | {{
                id: node.id,
                title: node.title,
                label: labels(node)[0]
            }}],
            links: [rel IN allRels WHERE rel IS NOT NULL | {{
                src: startNode(rel).id,
                dst: endNode(rel).id
            }}]
        }} AS graph
    """
    records = conn.query(
        query=query,
        db="neo4j"
    )
    return records[0]['graph'] if records else None


def list_indexes():
    query = """
        SHOW INDEXES
    """
    records = conn.query(
        query=query,
        db="neo4j"
    )
    return records


def create_index(label, property='embedding'):
    query = f"""
        CREATE VECTOR INDEX `{label}_embeddings` IF NOT EXISTS
        FOR (n:{label})
        ON (n.{property})
        OPTIONS {{indexConfig: {{
            `vector.dimensions`: { Config.OPENAI_EMBEDDING_DIMENSIONS },
            `vector.similarity_function`: 'cosine'
        }}}}
    """
    records = conn.query(
        query=query,
        db="neo4j"
    )
    return records