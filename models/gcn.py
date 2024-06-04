import torch
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv
from torch.nn import functional as F
from torch_geometric.utils import k_hop_subgraph


class GCN(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(GCN, self).__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)
        self.num_hops = sum(1 for layer in self.children() if isinstance(layer, GCNConv)) + 1
        self.optimizer = None
        self.loss_fn = None

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, training=self.training)
        x = self.conv2(x, edge_index)
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
                acc = self.evaluate(data)
                print(f'Epoch {epoch}, Loss: {loss:.4f}, Test Accuracy: {acc:.4f}')

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
        self.eval()
        with torch.no_grad():
            out = self(data)
            pred = out.argmax(dim=1)
            correct = pred[data.test_mask] == data.y[data.test_mask]
            acc = int(correct.sum()) / int(data.test_mask.sum())
            return acc
    
    def load_for_inference(self, path):
        self.load_state_dict(torch.load(path))
        self.eval()