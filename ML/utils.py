import numpy as np
import math
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from datagen import *


# PyTorch dataset class used to create dataloaders for model training, validation, and testing.
class TracesDataset(Dataset):

    def __init__(self, x, y, device):
        self.x = torch.from_numpy(x).float().to(device=device)
        self.y = torch.from_numpy(y).to(device=device)

    '''
    The __len__ function returns the number of samples in the dataset. In our case, array 'x' is the traces and the array 'y' is corresponding Hamming Weight.
    These two arrays are of equal length so we can return the length of anyone. It is used internally by PyTorch while loading data.
    '''

    def __len__(self):
        return len(self.x)

    '''
    The __getitem__ function returns a trace and its corresponding Hamming Weight. It is used internally by PyTorch while loading data.
    '''

    def __getitem__(self, item):
        return self.x[item], self.y[item]


def get_activation_fn(activation):
    '''
    This function maps a string of the activation function to the exact function name in PyTorch.
    '''
    activation_dict = {
        'relu': 'ReLU',
        'prelu': 'PReLU',
        'elu': 'ELU',
        'leakyrelu': 'LeakyReLU',
        'selu': 'SeLU',
        'celu': 'CeLU',
        'silu': 'SiLU',
        'sigmoid': 'Sigmoid',
        'gelu': 'GeLU',
        'relu6': 'ReLU6',
        'rrelu': 'RReLU',
        'tanh': 'Tanh'
    }
    activation_fn = activation_dict[activation.lower()]

    return activation_fn


def get_optimizer_fn(optim):
    '''
    This function maps a string of the optimizater to the exact optimizer name in PyTorch.
    '''
    optim_dict = {
        'adadelta': 'Adadelta',
        'adagrad': 'Adagrad',
        'adam': 'Adam',
        'adamw': 'AdamW',
        'sparseadam': 'SparseAdam',
        'adamax': 'Adamax',
        'asgd': 'ASGD',
        'lbfgs': 'LBFGS',
        'rmsprop': 'RMSprop',
        'pprop': 'Rprop',
        'sgd': 'SGD'
    }
    optim_fn = optim_dict[optim.lower()]

    return optim_fn


def load_and_split_data(train_split, val_split, test_split, datasize=-1, stddev=-1):
    '''
    This function loads the traces dataset, randomly permutes it, and creates train/val/test splits.
    '''
    X, y = load_full_data()
    snr = -1

    perm = np.random.permutation(len(X))
    X = X[perm]
    y = y[perm]

    if datasize != -1:
        X = X[:datasize]
        y = y[:datasize]

    if stddev != -1:
        # Additive white Gaussian noise added to traces to simulate low SNR
        X = X + np.random.normal(0, stddev, X.shape)
        snr = calc_snr(y, X)

    assert(train_split + val_split + test_split == 1.0)

    X_train, X_val, X_test = np.split(
        X, [int(train_split * len(X)), int((train_split + val_split) * len(X))])
    y_train, y_val, y_test = np.split(
        y, [int(train_split * len(y)), int((train_split + val_split) * len(y))])

    return X_train, X_val, X_test, y_train, y_val, y_test, snr


def create_model(input_shape, hidden, dropout, activation, output_shape=33):
    '''
    This function creates a MLP model from the provided configuration.
    '''
    modules = []
    modules.extend([nn.Linear(input_shape, hidden[0]),
                    getattr(nn, activation)(), nn.Dropout(p=dropout[0])])

    for i in range(len(hidden) - 1):
        try:
            modules.extend([nn.Linear(hidden[i], hidden[i + 1]),
                            getattr(nn, activation)(), nn.Dropout(p=dropout[i + 1])])
        except:
            modules.extend([nn.Linear(hidden[i], hidden[i + 1]),
                            getattr(nn, activation)()])

    modules.extend([nn.Linear(hidden[-1], output_shape)])

    return modules


def calc_snr(label, traces):
    '''
    This function calculates Signal-to-Noise Ratio (SNR) of the leakage, indicated by the equation SNR = Var(E[Trace|L=l])/E[Var(Trace|L=l)], where l is the label (Hamming weight or identity)
    The inputs to this function are the label array (length N) and the traces matrix (N x T), where N is the number of traces and T is the number of time samples for the trace
    The function will first obtain the SNR over each time sample, and then return the max value
    '''

    unique_list = np.unique(label)
    counter_unique = np.zeros(len(unique_list))

    # for mean or Expectation E
    mean_unique = np.zeros((len(unique_list), traces.shape[1]))
    var_unique = np.zeros(
        (len(unique_list), traces.shape[1]))  # for Variance Var

    for i in range(len(unique_list)):
        temp = unique_list[i]
        idx = np.where(label == temp)[0]
        counter_unique[i] = len(idx)

        for j in range(traces.shape[1]):
            mean_unique[i, j] = np.mean(traces[idx, j])
            var_unique[i, j] = np.var(traces[idx, j])

    s_n_r = np.zeros(traces.shape[1])
    for i in range(traces.shape[1]):
        s_n_r[i] = np.var(mean_unique[:, i])/np.mean(var_unique[:, i])

    return np.max(s_n_r)
