from models.neo4j_connection import conn
from utils.helpers import generate_id
from datetime import datetime, timezone


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
            if key == 'start_date':
                filter_conditions.append(f"n.created_at >= datetime(${key})")
            elif key == 'end_date':
                filter_conditions.append(f"n.created_at <= datetime(${key})")
            else:
                filter_conditions.append(f"n.{key} = ${key}")
        where_clause = "WHERE " + " AND ".join(filter_conditions)
    
    label_clause = f":{label}" if label else ""
    
    query = f"""
        MATCH (n{label_clause})
        {where_clause}
        RETURN properties(n) AS node, labels(n) AS labels
        ORDER BY n.created_at DESC
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


def get_recent_nodes():
    query = """
        MATCH (n)
        RETURN n.id AS id, n.title AS title, n.created_at AS created_at
        ORDER BY n.created_at DESC
        LIMIT 5
    """
    records = conn.query(
        query=query,
        db="neo4j"
    )
    return records