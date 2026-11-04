# Import libraries
import csv
import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

# Device configuration (MPS for Apple Silicon Mac, CUDA, or CPU)
if torch.backends.mps.is_available():
    device = torch.device('mps')
elif torch.cuda.is_available():
    device = torch.device('cuda')
else:
    device = torch.device('cpu')

print(f'Using {device}')

# Configure and Hyperparameters
SEED = 42


def set_seed(seed: int = 42):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


if __name__ == '__main__':
    set_seed(SEED)
    print(f'Baseline initialized. Random seed: {SEED}')
