from datagen import *
from utils import *

import configparser
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.utils import class_weight
import os
import shutil
import platform
import datetime
import json
import re

import optuna
from optuna.trial import TrialState


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load config file
config = configparser.ConfigParser()
config.read('config.ini')

# Logging information
init_time = time.time()
curr_time = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
logfile = open("trace_logs_opt.log", "a+", buffering=1)
print("\n\nTime: %s\n" % curr_time)
logfile.write("\n\nTime: %s\n" % curr_time)
print("Platform information: %s, %s" % (platform.platform(), platform.node()))
logfile.write("Platform information: %s, %s\n" %
              (platform.platform(), platform.node()))
print("PyTorch version: %s" % torch.__version__)
logfile.write("PyTorch version: %s\n" % torch.__version__)
print("Numpy version: %s" % np.__version__)
logfile.write("Numpy version: %s\n" % np.__version__)
print("Python information: %s" % platform.python_version())
print("Config information: %s\n" % json.dumps(config._sections, indent=4))
logfile.write("Config information: %s \n" %
              json.dumps(config._sections, indent=4))
try:
    gpu_memory = torch.cuda.get_device_properties(0).total_memory
    print("Total GPU memory: %s bytes\n" % gpu_memory)
    logfile.write("Total GPU memory: %s bytes\n\n" % gpu_memory)
except:
    print("No GPU\n")
    logfile.write("No GPU\n")

path = "traces_models_opt"
if os.path.exists(path):
    shutil.rmtree(path)
os.mkdir(path)

path += "/"

X, y = load_optuna_data()

# Ensure train and val are not same across runs
perm = np.random.permutation(len(X))
X_glob = X[perm]
y_glob = y[perm]

best_trial_number = 0
best_trial_acc = 0.0

# Load parameters from config file
n_layers_l = int(config['OPTUNA']['NumLayers'].split()[0])
n_layers_u = int(config['OPTUNA']['NumLayers'].split()[1])
size_layers_l = int(config['OPTUNA']['LayerSize'].split()[0])
size_layers_u = int(config['OPTUNA']['LayerSize'].split()[1])
epochs = int(config['OPTUNA']['Epochs'])
batch_size = int(config['OPTUNA']['BatchSize'])
learning_rate = float(config['OPTUNA']['LR'])
train_split = float(config['OPTUNA']['Train'])
val_split = float(config['OPTUNA']['Val'])
acc_eps = float(config['OPTUNA']['AccuracyEps'])

# Load parameters from config file
hidden = list(map(int, config['ML']['Hidden'].split(' ')))
epochs = int(config['ML']['Epochs'])


X_train, X_val = np.split(X_glob, [int(train_split * len(X_glob))])
y_train, y_val = np.split(y_glob, [int(train_split * len(y_glob))])

# Compute class weights for weighted cross entropy loss
class_weights = class_weight.compute_class_weight('balanced',
                                                  classes=np.arange(33),
                                                  y=y_train)

weights = torch.tensor(class_weights, dtype=torch.float32).to(device)

# Prepare datasets for training and validation
train_set = TracesDataset(X_train, y_train, device)
train_loader = DataLoader(
    dataset=train_set, batch_size=batch_size, shuffle=False)

val_set = TracesDataset(X_val, y_val, device)
val_loader = DataLoader(dataset=val_set, batch_size=batch_size, shuffle=False)


# Creates a model for trial
def define_model(trial):

    activation = get_activation_fn(config['OPTUNA']['Activation'])

    n_layers = trial.suggest_int("n_layers", n_layers_l, n_layers_u)
    layers = []

    hidden_size = trial.suggest_int(
        "hidden_size", size_layers_l, size_layers_u, step=32)

    # Create MLP model
    in_features = 500
    for i in range(n_layers):
        out_features = hidden_size
        layers.append(nn.Linear(in_features, out_features))
        layers.append(getattr(nn, activation)())

        in_features = out_features

    layers.append(nn.Linear(in_features, 33))

    return nn.Sequential(*layers)


# Objective function to optimize is the validation accuracy
def objective(trial):

    # Retrieve model with chosen hyperparameters
    model = define_model(trial)
    model.to(device)

    lr = float(config['OPTUNA']['LR'])
    optimizer = getattr(torch.optim, get_optimizer_fn(config['OPTUNA']['Optimizer']))(
        model.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss(weight=weights)

    final_acc = 0.0
    probs = nn.Softmax(dim=1)
    # Train model
    train_start = time.time()
    for i in range(epochs):
        model.train()
        train_loss = 0.0
        train_acc = 0.0
        cnt = 0
        for x, y in train_loader:
            cnt += 1
            pred = model(x)

            loss = loss_fn(pred, y)
            train_loss += loss.item()

            # Accuracy computation using "eps" tolerance
            correct_pred = torch.isclose(
                probs(pred).argmax(dim=1), y, atol=acc_eps, rtol=0.0)
            train_acc += correct_pred.float().sum() / len(correct_pred)

            optimizer.zero_grad()

            loss.backward()
            optimizer.step()

        train_loss /= len(train_loader)
        train_acc /= len(train_loader)

        model.eval()
        val_loss = 0.0
        val_acc = 0.0
        # Validate model
        with torch.no_grad():
            for x, y in val_loader:
                pred = model(x)

                loss = loss_fn(pred, y)

                # Accuracy computation using "eps" tolerance
                correct_pred = torch.isclose(
                    probs(pred).argmax(dim=1), y, atol=acc_eps, rtol=0.0)
                val_acc += correct_pred.float().sum() / len(correct_pred)

                val_loss += loss.item()

        val_loss /= len(val_loader)
        val_acc /= len(val_loader)

        if trial.should_prune():
            raise optuna.exceptions.TrialPruned()

    torch.save(model, path + "traces_" + str(round(val_acc.item(), 5)
                                             ) + '_' + str(trial.number) + '.pth')

    print("\nTrial {} Train Accuracy: {}".format(trial.number, train_acc))

    logfile.write("\nTrial number: {}\n".format(trial.number))
    logfile.write("Trial Train accuracy: {}\n".format(train_acc))
    logfile.write("Trial Val accuracy: {}\n".format(val_acc))
    logfile.write("Params: \n")
    for key, value in trial.params.items():
        logfile.write("    {}: {}\n".format(key, value))

    global best_trial_number, best_trial_acc

    if val_acc > best_trial_acc:
        best_trial_acc = val_acc
        best_trial_number = trial.number
        logfile.write("Best trial is {} with Val accuracy: {}\n".format(
            best_trial_number, val_acc))

    return val_acc


# Run trials to find optimal model
def run_optuna():
    n_trials = int(config['OPTUNA']['Trials'])

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)

    pruned_trials = study.get_trials(
        deepcopy=False, states=[TrialState.PRUNED])
    complete_trials = study.get_trials(
        deepcopy=False, states=[TrialState.COMPLETE])

    print("Study statistics: ")
    logfile.write("Study statistics: \n")
    print("  Number of finished trials: ", len(study.trials))
    logfile.write(
        "  Number of finished trials: {}\n".format(len(study.trials)))
    print("  Number of pruned trials: ", len(pruned_trials))
    logfile.write("  Number of pruned trials: {}\n".format(len(pruned_trials)))
    print("  Number of complete trials: ", len(complete_trials))
    logfile.write("  Number of complete trials: {}\n".format(
        len(complete_trials)))

    print("Best trial:")
    trial = study.best_trial
    logfile.write("Best trial:\n")

    print("  Value: ", trial.value)
    logfile.write("  Value: {}\n".format(trial.value))

    print("  Params: ")
    logfile.write(" Params: \n")
    for key, value in trial.params.items():
        print("    {}: {}".format(key, value))
        logfile.write("    {}: {}\n".format(key, value))

    logfile.close()


if __name__ == "__main__":
    run_optuna()
