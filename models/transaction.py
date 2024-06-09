from .gnn import GNN
from torch_geometric.nn import GCNConv, GATConv
import torch

class TransactionClassifierGCN(GNN):
    def __init__(self):
        GNN.__init__(self, layers=[GCNConv(165, 100), GCNConv(100, 2)])
        class_weights = [0.3, 0.7]
        self.optimizer = torch.optim.Adam(self.parameters(), lr=1e-3, weight_decay=5e-4)
        self.compile(self.optimizer, torch.nn.CrossEntropyLoss, class_weights)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.to(device)

class TransactionClassifierGAT(GNN):
    def __init__(self):
        GNN.__init__(self, layers=[GATConv(165, 100), GATConv(100, 2)])
        class_weights = [0.3, 0.7]
        self.optimizer = torch.optim.Adam(self.parameters(), lr=1e-3, weight_decay=5e-4)
        self.compile(self.optimizer, torch.nn.CrossEntropyLoss, class_weights)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.to(device)