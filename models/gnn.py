import torch
from torch_geometric.data import Data
from torch.nn import functional as F
from torch_geometric.utils import k_hop_subgraph
from sklearn.metrics import classification_report


class GNN(torch.nn.Module):
    def __init__(self, layers):
        super(GNN, self).__init__()
        self.layers = layers
        self.num_hops = sum(['Conv' in layer.__class__.__name__ for layer in layers])
        self.optimizer = None
        self.loss_fn = None

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        for layer in self.layers:
            if 'Conv' in layer.__class__.__name__:
                x = layer(x, edge_index)
            else:
                x = layer(x)
        return x

    def compile(self, optimizer, loss_fn, class_weights=None):
        self.optimizer = optimizer
        if class_weights is not None:
            class_weights_tensor = torch.tensor(class_weights, dtype=torch.float).to(next(self.parameters()).device)
            self.loss_fn = loss_fn(weight=class_weights_tensor)
        else:
            self.loss_fn = loss_fn()

    def fit(self, data, epochs=1000):
        for epoch in range(epochs):
            self.train()
            self.optimizer.zero_grad()
            out = self(data)
            loss = self.loss_fn(out[data.train_mask], data.y[data.train_mask])
            loss.backward()
            self.optimizer.step()

            if epoch % 100 == 0:
                print(f"Epoch {epoch}")
    
    def predict(self, data, node_idx=None):
        self.eval()
        with torch.no_grad():
            if node_idx is not None:
                subset, edge_index, mapping, _ = k_hop_subgraph(node_idx, self.num_hops, data.edge_index, relabel_nodes=True)
                sub_data = Data(x=data.x[subset], edge_index=edge_index)
            else:
                sub_data = data
            out = self(sub_data)
        return out

    def evaluate(self, data):
        raise NotImplementedError
    
    def load_for_inference(self, path):
        self.load_state_dict(torch.load(path))
        self.eval()


class GNNClassifier(GNN):
    def __init__(self, layers):
        super(GNN, self).__init__()

    def predict(self, data, node_idx=None):
        self.eval()
        with torch.no_grad():
            if node_idx is not None:
                subset, edge_index, mapping, _ = k_hop_subgraph(node_idx, self.num_hops, data.edge_index, relabel_nodes=True)
                sub_data = Data(x=data.x[subset], edge_index=edge_index)
            else:
                sub_data = data
            out = self(sub_data)
            probabilities = F.softmax(out, dim=1)
            predictions = probabilities.argmax(dim=1)
            if node_idx is not None:
                return predictions[mapping.item()], probabilities[mapping.item()]
            else:
                return predictions, probabilities
    
    def evaluate(self, data):
        predictions = self.predict(data)[0][data.test_mask].detach().cpu().numpy()
        true_labels = data.y[data.test_mask].detach().cpu().numpy()
        return classification_report(true_labels, predictions, output_dict=True)