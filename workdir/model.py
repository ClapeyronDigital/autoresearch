import torch.nn as nn

from abstract import ModelBase


HIDDEN_DIM = 128
N_LAYERS = 1
ACTIVATION = "relu"
DROPOUT = 0.0
BATCH_NORM = False


def get_activation(name):
    if name == "relu":
        return nn.ReLU()
    elif name == "gelu":
        return nn.GELU()
    elif name == "silu":
        return nn.SiLU()
    raise ValueError(f"Unknown activation: {name}")


class Model(ModelBase, nn.Module):
    def __init__(self):
        nn.Module.__init__(self)
        layers = []
        in_dim = 784
        for _ in range(N_LAYERS):
            layers.append(nn.Linear(in_dim, HIDDEN_DIM))
            if BATCH_NORM:
                layers.append(nn.BatchNorm1d(HIDDEN_DIM))
            layers.append(get_activation(ACTIVATION))
            if DROPOUT > 0:
                layers.append(nn.Dropout(DROPOUT))
            in_dim = HIDDEN_DIM
        layers.append(nn.Linear(in_dim, 10))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        x = x.view(x.size(0), -1)
        return self.net(x)

    def predict(self, x):
        return self.forward(x)
