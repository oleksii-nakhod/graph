from models.neo4j_connection import conn
from utils.helpers import generate_id, create_openai_embedding, create_item_embedding
from datetime import datetime, timezone
from config import Config
import cProfile
import pstats
import time


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


def list_nodes(filters=None, query="", page=1, page_size=10, sort_by='created_at', sort_order='DESC', start_date=None, end_date=None):
    skip = (page - 1) * page_size
    labels = filters.pop('labels', []) if filters else []
    where_clause = ""
    filter_conditions = []
    
    if filters:
        for key, value in filters.items():
            filter_conditions.append(f"n.{key} = ${key}")

    if labels:
        label_conditions = [f"'{label}' IN labels(n)" for label in labels]
        filter_conditions.extend(label_conditions)
        
    if start_date:
        filter_conditions.append("n.created_at >= $start_date")
    
    if end_date:
        filter_conditions.append("n.created_at <= $end_date")

    if filter_conditions:
        where_clause = "WHERE " + " AND ".join(filter_conditions)
    
    if query:
        neo4j_query = f"""
            CALL db.index.vector.queryNodes('item_embedding_index', {page * page_size}, $embedding) 
            YIELD node AS n, score
            {where_clause}
            
            WITH n, score
            ORDER BY score DESC, n.{sort_by} {sort_order}, n.id ASC
            
            SKIP {skip} LIMIT {page_size}
            
            RETURN properties(n) AS properties, labels(n) AS labels, score
        """
    else:
        neo4j_query = f"""
            MATCH (n)
            {where_clause}
            
            WITH n
            ORDER BY n.{sort_by} {sort_order}, n.id ASC
            
            SKIP {skip} LIMIT {page_size}
            
            RETURN properties(n) AS properties, labels(n) AS labels
        """
    
    parameters = filters.copy() if filters else {}
    parameters.update({
        'embedding': create_openai_embedding(query),
        'start_date': start_date,
        'end_date': end_date
    })
    
    records = conn.query(
        query=neo4j_query,
        parameters=parameters,
        db="neo4j"
    )
    results = []
    for record in records:
        node = record['properties']
        node['labels'] = record['labels']
        node['score'] = record.get('score', None)
        node.pop('embedding', None)
        results.append(node)
    
    return results


def create_node(properties):
    labels = properties.pop('labels', [])
    labels.append('Item')
    
    slug = properties.pop('slug', None)
    title = properties.pop('title', None)
    content = properties.pop('content', None)
    
    properties['id'] = generate_id(labels=labels, slug=slug)
    
    properties['title'] = title
    properties['content'] = content
    time_now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    properties['created_at'] = time_now
    properties['updated_at'] = time_now
    properties['embedding'] = create_item_embedding({
        'title': title,
        'labels': labels,
        'content': content
    })
    
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
    time_now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    labels = properties.pop('labels', [])
    label_clause = f", n:{':'.join(labels)}" if labels else ""
    title = properties.pop('title', None)
    content = properties.pop('content', None)
    
    properties['title'] = title
    properties['content'] = content
    
    properties['updated_at'] = time_now
    properties['embedding'] = create_item_embedding({
        'title': title,
        'labels': labels,
        'content': content
    })
    
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


def create_node_batch(nodes):
    time_now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    for node in nodes:
        slug = node.pop('slug', None)
        title = node.pop('title', None)
        content = node.pop('content', None)
        
        node['labels'].append('Item')
        
        embedding = create_item_embedding({
            'title': title,
            'labels': node['labels'],
            'content': content
        })
        
        node.update({
            'id': generate_id(labels=node['labels'], slug=slug),
            'title': title,
            'content': content,
            'created_at': time_now,
            'updated_at': time_now,
            'embedding': embedding
        })
    query = f"""
        UNWIND $batch AS node
        CREATE (n)
        SET n = node.properties
        WITH n, node
        CALL apoc.create.addLabels(n, node.labels)
        YIELD node AS updatedNode
        RETURN updatedNode.id AS id
    """

    parameters = {'batch': [{'properties': node, 'labels': node.pop('labels')} for node in nodes]}
    
    records = conn.query(
        query=query,
        parameters=parameters,
        db="neo4j"
    )
        
    return [{'id': record['id']} for record in records]


def get_edge(id):
    query = """
        MATCH (src)-[r]->(dst)
        WHERE r.id = $id
        RETURN properties(r) AS properties, type(r) AS type, src.id AS src, dst.id AS dst
    """
    records = conn.query(
        query=query,
        parameters={'id': id},
        db="neo4j"
    )
    if records:
        edge = records[0]['properties']
        edge.update({
            'src': records[0]['src'],
            'dst': records[0]['dst'],
            'type': records[0]['type']
        })
        return edge


def list_edges(filters=None, page=1, page_size=10, sort_by='created_at', sort_order='DESC', start_date=None, end_date=None):
    skip = (page - 1) * page_size
    relationship_type = filters.pop('type', None) if filters else None
    where_clause = ""
    filter_conditions = []
    
    if filters:
        for key, value in filters.items():
            filter_conditions.append(f"r.{key} = ${key}")

    if relationship_type:
        filter_conditions.extend([f"type(r) = '{relationship_type}'"])
        
    if start_date:
        filter_conditions.append("r.created_at >= $start_date")
    
    if end_date:
        filter_conditions.append("r.created_at <= $end_date")

    if filter_conditions:
        where_clause = "WHERE " + " AND ".join(filter_conditions)
    
    neo4j_query = f"""
        MATCH (src)-[r]->(dst)
        {where_clause}
        
        WITH r, src, dst
        ORDER BY r.{sort_by} {sort_order}, r.id ASC
        
        SKIP {skip} LIMIT {page_size}
        
        RETURN properties(r) AS properties, type(r) AS type, src.id AS src, dst.id AS dst
    """
    
    parameters = filters.copy() if filters else {}
    parameters.update({
        'start_date': start_date,
        'end_date': end_date
    })
    
    records = conn.query(
        query=neo4j_query,
        parameters=parameters,
        db="neo4j"
    )
    results = []
    for record in records:
        edge = record['properties']
        edge.update({
            'src': record['src'],
            'dst': record['dst'],
            'type': record['type']
        })
        
        results.append(edge)
    
    return results


def create_edge(properties):
    time_now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    src_id = properties.pop('src', None)
    dst_id = properties.pop('dst', None)
    edge_type = properties.pop('type', 'RELATED')
    slug = properties.pop('slug', None)
    
    properties['id'] = generate_id(labels=[edge_type], slug=slug)
    properties['created_at'] = time_now
    properties['updated_at'] = time_now
    
    query = f"""
        MATCH (src), (dst)
        WHERE src.id = $src_id AND dst.id = $dst_id
        CREATE (src)-[r:{edge_type} $properties]->(dst)
        RETURN r.id AS id
    """
    records = conn.query(
        query=query,
        parameters={'src_id': src_id, 'dst_id': dst_id, 'properties': properties},
        db="neo4j"
    )
    if records:
        return {
            'id': records[0]['id']
        }
    else:
        return None


def create_edge_batch(edges):
    time_now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    for edge in edges:
        edge_type = edge.get('type', 'RELATED')
        slug = edge.pop('slug', None)
        
        edge.update({
            'id': generate_id(labels=[edge_type], slug=slug),
            'created_at': time_now,
            'updated_at': time_now
        })
    
    query = """
        UNWIND $batch AS edge
        MATCH (src:Item {id: edge.src}), (dst:Item {id: edge.dst})
        CALL apoc.create.relationship(src, edge.type, edge.properties, dst) YIELD rel
        RETURN rel.id AS id
    """
    
    parameters = {'batch': [{'src': edge['src'], 'dst': edge['dst'], 'properties': edge, 'type': edge.pop('type', 'RELATED')} for edge in edges]}
    
    records = conn.query(
        query=query,
        parameters=parameters,
        db="neo4j"
    )
    
    return [{'id': record['id']} for record in records]



def profile_function(nodes):
    profiler = cProfile.Profile()
    profiler.enable()
    res = create_node_batch(nodes)
    profiler.disable()
    
    stats = pstats.Stats(profiler)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()
    return res


def list_node_labels():
    query = """
        CALL db.labels()
    """
    records = conn.query(
        query=query,
        db="neo4j"
    )
    return [record['label'] for record in records]


def get_graph_neighborhood(ids, node_limit=10, edge_limit=10):
    query = f"""
        WITH {ids} AS nodeIds
        MATCH (n)
        WHERE n.id IN nodeIds
        WITH n
        LIMIT {node_limit}
        OPTIONAL MATCH (n)-[r]-(m)
        WITH n, r, m
        LIMIT {edge_limit}
        WITH COLLECT(DISTINCT n) AS nodes, COLLECT(DISTINCT m) AS neighbors, COLLECT(DISTINCT r) AS relationships
        WITH apoc.coll.toSet(nodes + neighbors) AS uniqueNodes, relationships
        RETURN {{
            nodes: [node IN uniqueNodes WHERE node IS NOT NULL | {{
                id: node.id,
                title: node.title,
                labels: labels(node)
            }}],
            edges: [rel IN relationships WHERE rel IS NOT NULL | {{
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