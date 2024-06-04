import requests
import os
import pickle
import torch
from torch_geometric.data import Data

base_url = 'http://localhost:5004'
node_url = f"{base_url}/api/nodes"
edge_url = f"{base_url}/api/edges"
headers = {"Content-Type": "application/json"}
batch_size = 10_000
cache_file = 'data_cache.pkl'

def fetch_data(url, headers, batch_size, page):
    params = {"page_size": batch_size, "page": page}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def process_nodes(existing_nodes, new_nodes):
    node_id_map = {node['id']: idx for idx, node in enumerate(existing_nodes)}
    start_idx = len(existing_nodes)
    
    for node in new_nodes:
        if node['id'] not in node_id_map:
            node_id_map[node['id']] = start_idx
            existing_nodes.append(node)
            start_idx += 1

def process_edges(existing_edges, new_edges, existing_nodes):
    node_id_map = {node['id']: idx for idx, node in enumerate(existing_nodes)}

    for edge in new_edges:
        if edge['src'] in node_id_map and edge['dst'] in node_id_map:
            existing_edges.append(edge)

def save_cache(nodes, edges, node_page, edge_page):
    with open(cache_file, 'wb') as f:
        pickle.dump((nodes, edges, node_page, edge_page), f)

def load_cache():
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    return None, None, 1, 1

def fetch_and_process_data():
    existing_nodes, existing_edges, node_page, edge_page = load_cache()

    if existing_nodes is None:
        existing_nodes = []
    if existing_edges is None:
        existing_edges = []

    try:
        while True:
            node_data = fetch_data(node_url, headers, batch_size, node_page)
            new_nodes = node_data['results']
            
            if not new_nodes:
                break
            
            process_nodes(existing_nodes, new_nodes)
            start_idx = (node_page - 1) * batch_size
            end_idx = start_idx + len(new_nodes) - 1
            print(f"Nodes {start_idx}-{end_idx} retrieved.")
            node_page += 1
            save_cache(existing_nodes, existing_edges, node_page, edge_page)

        while True:
            edge_data = fetch_data(edge_url, headers, batch_size, edge_page)
            new_edges = edge_data['results']
            
            if not new_edges:
                break
            
            process_edges(existing_edges, new_edges, existing_nodes)
            start_idx = (edge_page - 1) * batch_size
            end_idx = start_idx + len(new_edges) - 1
            print(f"Edges {start_idx}-{end_idx} retrieved.")
            edge_page += 1
            save_cache(existing_nodes, existing_edges, node_page, edge_page)

    except Exception as e:
        print(f"An error occurred: {e}")
        save_cache(existing_nodes, existing_edges, node_page, edge_page)
        raise

    return existing_nodes, existing_edges


def load_model(model_path):
    return torch.load(model_path)


def load_preprocessed_data(file_path):
    with open(file_path, 'rb') as f:
        preprocessed_data = pickle.load(f)
    return preprocessed_data


def create_data_object(nodes, edges):
    sorted_nodes = sorted(nodes, key=lambda node: node['orig_id'])
    sorted_edges = sorted(edges, key=lambda edge: edge['orig_id'])

    node_features = []
    node_labels = []
    node_id_map = {}

    for idx, node in enumerate(sorted_nodes):
        node_id_map[node['id']] = idx
        node_features.append(node['x'])
        node_labels.append(node['y'])

    node_features = torch.tensor(node_features, dtype=torch.float)
    node_labels = torch.tensor(node_labels, dtype=torch.long)

    edge_index = []
    for edge in sorted_edges:
        if edge['src'] in node_id_map and edge['dst'] in node_id_map:
            src = node_id_map[edge['src']]
            dst = node_id_map[edge['dst']]
            edge_index.append([src, dst])

    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()

    return Data(x=node_features, edge_index=edge_index, y=node_labels)