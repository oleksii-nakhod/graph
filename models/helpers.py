import requests
import os
import pickle
import torch
import json
from torch_geometric.data import Data


def read_n_to_last_line(filename, n=1):
    """Returns the nth before last line of a file (n=1 gives last line)
    https://stackoverflow.com/a/73195814
    """
    num_newlines = 0
    with open(filename, 'rb') as f:
        try:
            f.seek(-2, os.SEEK_END)
            while num_newlines < n:
                f.seek(-2, os.SEEK_CUR)
                if f.read(1) == b'\n':
                    num_newlines += 1
        except OSError:
            f.seek(0)
        last_line = f.readline().decode()
    return last_line


def load_node_id_map(file_path):
    node_id_map = {}
    with open(file_path, 'r') as file:
        for line in file:
            entry = json.loads(line)
            node_id_map[entry['orig_id']] = entry['new_id']
    return node_id_map


def get_node_orig_id(node_id_map, orig_id):
    return node_id_map.get(orig_id)


def upload_transaction_nodes(data, node_url, uploaded_nodes_file, batch_size):
    start_index = 0

    if os.path.exists(uploaded_nodes_file):
        last_line = read_n_to_last_line(uploaded_nodes_file, 1)
        start_index = json.loads(last_line)['orig_id'] + 1

    total_nodes = len(data.x)

    with requests.Session() as session:
        headers = {'Content-Type': 'application/json'}
        for start in range(start_index, total_nodes, batch_size):
            end = min(start + batch_size, total_nodes)
            nodes = []

            for i in range(start, end):
                node = {
                    'labels': ['Transaction'],
                    'x': data.x[i].tolist(),
                    'y': data.y[i].item(),
                    'orig_id': i,
                }
                nodes.append(node)

            try:
                response = session.post(node_url, json=nodes, headers=headers)
                response.raise_for_status()
                new_node_ids = response.json()
                with open(uploaded_nodes_file, 'a') as file:
                    for i, node in enumerate(new_node_ids):
                        json_line = json.dumps({'orig_id': start + i, 'new_id': node['id']})
                        file.write(json_line + '\n')
                print(f"Nodes {start} to {end - 1} created successfully")
            except requests.exceptions.RequestException as e:
                print(f"Failed to create nodes {start} to {end - 1}: {e}")


def upload_transaction_edges(data, edge_url, uploaded_edges_file, batch_size, node_id_map):
    
    edge_index = data.edge_index

    total_edges = edge_index.size(1)
    start_index = 0
    if os.path.exists(uploaded_edges_file):
        last_line = read_n_to_last_line(uploaded_edges_file, 1)
        start_index = json.loads(last_line)['orig_id'] + 1

    with requests.Session() as session:
        headers = {'Content-Type': 'application/json'}
        for start in range(start_index, total_edges, batch_size):
            end = min(start + batch_size, total_edges)
            edges = []

            for i in range(start, end):
                src_index = edge_index[0, i].item()
                dst_index = edge_index[1, i].item()

                src_id = get_node_orig_id(node_id_map, src_index)
                dst_id = get_node_orig_id(node_id_map, dst_index)

                if src_id is not None and dst_id is not None:
                    edge = {
                        'src': src_id,
                        'dst': dst_id,
                        'orig_id': i,
                    }
                    edges.append(edge)

            try:
                response = session.post(edge_url, json=edges, headers=headers)
                response.raise_for_status()
                edge_ids = response.json()
                with open(uploaded_edges_file, 'a') as file:
                    for i, edge in enumerate(edge_ids):
                        json_line = json.dumps({'orig_id': start + i, 'new_id': edge['id']})
                        file.write(json_line + '\n')
                print(f"Edges {start} to {end - 1} created successfully")
            except requests.exceptions.RequestException as e:
                print(f"Failed to create edges {start} to {end - 1}: {e}")


def fetch_data(url, batch_size, page, headers={'Content-Type': 'application/json'}):
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


def save_data(data, file_path):
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)


def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    return None


def fetch_and_process_graph_data(node_url, edge_url, file_path, batch_size):
    existing_nodes, existing_edges, node_page, edge_page = load_data(file_path)

    if existing_nodes is None:
        existing_nodes = []
    if existing_edges is None:
        existing_edges = []

    try:
        while True:
            node_data = fetch_data(node_url, batch_size, node_page)
            new_nodes = node_data['results']
            
            if not new_nodes:
                break
            
            process_nodes(existing_nodes, new_nodes)
            start_idx = (node_page - 1) * batch_size
            end_idx = start_idx + len(new_nodes) - 1
            print(f"Nodes {start_idx}-{end_idx} retrieved.")
            node_page += 1
            save_data((existing_nodes, existing_edges, node_page, edge_page), file_path)

        while True:
            edge_data = fetch_data(edge_url, batch_size, edge_page)
            new_edges = edge_data['results']
            
            if not new_edges:
                break
            
            process_edges(existing_edges, new_edges, existing_nodes)
            start_idx = (edge_page - 1) * batch_size
            end_idx = start_idx + len(new_edges) - 1
            print(f"Edges {start_idx}-{end_idx} retrieved.")
            edge_page += 1
            save_data((existing_nodes, existing_edges, node_page, edge_page), file_path)

    except Exception as e:
        print(f"An error occurred: {e}")
        save_data((existing_nodes, existing_edges, node_page, edge_page), file_path)
        raise

    return existing_nodes, existing_edges


def save_model(model, model_path):
    torch.save(model, model_path)


def load_model(model_path):
    return torch.load(model_path)


def load_preprocessed_data(file_path):
    with open(file_path, 'rb') as f:
        preprocessed_data = pickle.load(f)
    return preprocessed_data


def create_data_object(nodes, edges, train_mask=None, test_mask=None):
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

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    data = Data(x=node_features, edge_index=edge_index, y=node_labels, train_mask=train_mask, test_mask=test_mask).to(device)
    return data