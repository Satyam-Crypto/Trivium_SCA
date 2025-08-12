from os.path import exists
import glob

import numpy as np


# Compute Hamming Weight of integer
def hw(x):
    return bin(int(x)).count("1")


# Prepare dataset from raw data and save as numpy arrays
def prepare_full_data():

    X_full = None
    y_full = None

    for csv in glob.glob("data/traces3/*.csv"):

        data = np.loadtxt(open(csv, "rb"), delimiter=",", converters={
                          0: lambda s: int(s, 16), 1: lambda s: int(s, 16)})
        X, y = data[:, 2:], data[:, 0]

        y = np.array(list(map(hw, y)))

        if X_full is None:
            X_full = X
            y_full = y
        else:
            X_full = np.concatenate((X_full, X))
            y_full = np.concatenate((y_full, y))

    with open("traces_full_X.npy", "wb") as f:
        np.save(f, X_full)

    with open("traces_full_y.npy", "wb") as f:
        np.save(f, y_full)


# Load data saved as numpy arrays
def load_full_data():

    if exists("traces_full_X.npy") == False or exists("traces_full_y.npy") == False:
        prepare_full_data()

    with open("traces_full_X.npy", "rb") as f:
        X = np.load(f)

    with open("traces_full_y.npy", "rb") as f:
        y = np.load(f)

    return X, y


# Utility to append some CSV files to data saved as numpy arrays
def append_to_full_data(files):

    with open("traces_full_X.npy", "rb") as f:
        X = np.load(f)

    with open("traces_full_y.npy", "rb") as f:
        y = np.load(f)

    for csv in files:

        data = np.loadtxt(open(csv, "rb"), delimiter=",", converters={
                          0: lambda s: int(s, 16), 1: lambda s: int(s, 16)})
        X_new, y_new = data[:, 2:], data[:, 0]

        y_new = np.array(list(map(hw, y_new)))

        X = np.concatenate((X, X_new))
        y = np.concatenate((y, y_new))

    with open("traces_full_X.npy", "wb") as f:
        np.save(f, X)

    with open("traces_full_y.npy", "wb") as f:
        np.save(f, y)


# Prepare dataset from raw data and save as numpy arrays
def prepare_optuna_data():

    X_full = None
    y_full = None

    for csv in glob.glob("data/*.csv"):

        data = np.loadtxt(open(csv, "rb"), delimiter=",", converters={
                          0: lambda s: int(s, 16), 1: lambda s: int(s, 16)})
        X, y = data[:, 2:], data[:, 0]

        y = np.array(list(map(hw, y)))

        if X_full is None:
            X_full = X
            y_full = y
        else:
            X_full = np.concatenate((X_full, X))
            y_full = np.concatenate((y_full, y))

    with open("traces_optuna_X.npy", "wb") as f:
        np.save(f, X_full)

    with open("traces_optuna_y.npy", "wb") as f:
        np.save(f, y_full)


# Load data saved as numpy arrays
def load_optuna_data():

    if exists("traces_optuna_X.npy") == False or exists("traces_optuna_y.npy") == False:
        prepare_optuna_data()

    with open("traces_optuna_X.npy", "rb") as f:
        X = np.load(f)

    with open("traces_optuna_y.npy", "rb") as f:
        y = np.load(f)

    return X, y
