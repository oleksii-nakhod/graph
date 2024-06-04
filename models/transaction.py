from .gcn import GCN
import torch

class TransactionClassifier(GCN):
    def __init__(self, in_channels=165, hidden_channels=100, out_channels=2):
        super(TransactionClassifier, self).__init__(in_channels, hidden_channels, out_channels)
        class_weights = [0.3, 0.7]
        self.optimizer = torch.optim.Adam(self.parameters(), lr=1e-3, weight_decay=5e-4)
        self.compile(self.optimizer, torch.nn.CrossEntropyLoss, class_weights)
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.to(device)