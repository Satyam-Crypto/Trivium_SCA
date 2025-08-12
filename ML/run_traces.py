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
import math

from utils import *

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load config file
config = configparser.ConfigParser()
config.read('config.ini')

# Logging information
init_time = time.time()
curr_time = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
logfile = open("trace_logs.log", "a+", buffering=1)
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
    logfile.write("Total GPU memory: %s bytes\n" % gpu_memory)
except:
    print("No GPU\n")
    logfile.write("No GPU\n")

# Load parameters from config file
hidden = list(map(int, config['ML']['Hidden'].split(' ')))
epochs = int(config['ML']['Epochs'])
acc_eps = float(config['ML']['AccuracyEps'])
dropout = list(map(float, config['ML']['Dropout'].split(' ')))
learning_rate = float(config['ML']['LR'])
batch_size = int(config['ML']['BatchSize'])
activation = config['ML']['Activation']
optim = config['ML']['Optimizer']
datasize = int(config['ML']['DatasetSize'])

path = "traces_models"
if os.path.exists(path):
    shutil.rmtree(path)
os.mkdir(path)

path += "/"

activation = get_activation_fn(activation)

optim = get_optimizer_fn(optim)

data_start = time.time()

train_split = float(config['ML']['Train'])
val_split = float(config['ML']['Val'])
test_split = float(config['ML']['Test'])

assert(train_split + val_split + test_split == 1.0)

X_train, X_val, X_test, y_train, y_val, y_test, _ = load_and_split_data(
    train_split, val_split, test_split, datasize)

# Log information about different data splits
print("Total dataset size: ")
print("{} = 2 ^ {}".format(len(X_train) + len(X_val) + len(X_test),
      math.log2(len(X_train) + len(X_val) + len(X_test))))
logfile.write("\nTotal dataset size: \n")
logfile.write("{} = 2 ^ {}\n".format(len(X_train) + len(X_val) +
              len(X_test), math.log2(len(X_train) + len(X_val) + len(X_test))))

print("Train samples: ")
print("{} = 2 ^ {}".format(len(X_train), math.log2(len(X_train))))
logfile.write("\nTrain samples: \n")
logfile.write("{} = 2 ^ {}\n".format(len(X_train), math.log2(len(X_train))))

print("Val samples: ")
print("{} = 2 ^ {}".format(len(X_val), math.log2(len(X_val))))
logfile.write("\nVal samples: \n")
logfile.write("{} = 2 ^ {}\n".format(len(X_val), math.log2(len(X_val))))

print("Test samples: ")
print("{} = 2 ^ {}".format(len(X_test), math.log2(len(X_test))))
logfile.write("\nTest samples: \n")
logfile.write("{} = 2 ^ {}\n".format(len(X_test), math.log2(len(X_test))))

unique, counts = np.unique(y_train, return_counts=True)
dist_train = dict(zip(unique, counts))

unique, counts = np.unique(y_val, return_counts=True)
dist_val = dict(zip(unique, counts))

unique, counts = np.unique(y_test, return_counts=True)
dist_test = dict(zip(unique, counts))

print("\nTrain distribution: \n")
print(dist_train)
logfile.write("\nTrain distribution: \n")
logfile.write(str(dist_train))

print("\nVal distribution: \n")
print(dist_val)
logfile.write("\nVal distribution: \n")
logfile.write(str(dist_val))

print("\nTest distribution: \n")
print(dist_test)
logfile.write("\nTest distribution: \n")
logfile.write(str(dist_test))

# Compute class weights for weighted cross entropy loss
class_weights = class_weight.compute_class_weight('balanced',
                                                  classes=np.arange(33),
                                                  y=y_train)

weights = torch.tensor(class_weights, dtype=torch.float32).to(device)

data_end = time.time()

print("Data preparation time: %s" % (data_end - data_start))
logfile.write("Data preparation time: %s\n" % (data_end - data_start))

print("Activation function: ", activation)
logfile.write("Activation function: %s\n" % activation)
print("Optimizer function: ", optim)
logfile.write("Optimizer function: %s\n" % optim)
print("Epochs: ", epochs)
logfile.write("Epochs: %s\n" % epochs)
print("Batch size: ", batch_size)
logfile.write("Batch size: %s\n" % batch_size)
print("Learning rate: ", learning_rate)
logfile.write("Learning rate: %s\n" % learning_rate)
print("Accuracy tolerance: ", acc_eps)
logfile.write("Accuracy tolernace: %s\n" % acc_eps)

modules = create_model(X_train.shape[1], hidden, dropout, activation, 33)

model = nn.Sequential(*modules)
print("Model Information: ")
print(model)
logfile.write("Model Information: \n%s\n" % model)
# Number of trainable parameters
print("Trainable Parameters: ", sum(p.numel()
      for p in model.parameters() if p.requires_grad))
logfile.write("Trainable Parameters: %s\n" % sum(p.numel()
              for p in model.parameters() if p.requires_grad))


model.to(device)

# Set loss function and optimizer
loss_fn = nn.CrossEntropyLoss(weight=weights)
optimizer = getattr(torch.optim, optim)(model.parameters(), lr=learning_rate)

# Prepare datasets for training, validation, and testing
train_set = TracesDataset(X_train, y_train, device)
train_loader = DataLoader(
    dataset=train_set, batch_size=batch_size, shuffle=False)

val_set = TracesDataset(X_val, y_val, device)
val_loader = DataLoader(dataset=val_set, batch_size=batch_size, shuffle=False)

test_set = TracesDataset(X_test, y_test, device)
test_loader = DataLoader(
    dataset=test_set, batch_size=batch_size, shuffle=False)

try:
    allocated_memory = torch.cuda.memory_allocated(0)
    print("Allocated GPU memory: %s bytes" % allocated_memory)
    logfile.write("Allocated GPU memory: %s bytes\n" % allocated_memory)
except:
    pass

final_acc = 0.0
probs = nn.Softmax(dim=1)
# Train model
train_start = time.time()
for i in range(epochs):
    model.train()
    train_loss = 0.0
    train_acc = 0.0

    for x, y in train_loader:
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

    print("Epoch {}/{}: Train Loss - {:.5f}, Val Loss - {:.5f}, Train Acc - {:.5f}, Val Acc - {:.5f}".format(
        i + 1, epochs, train_loss, val_loss, train_acc, val_acc))
    logfile.write("Epoch {}/{}: Train Loss - {:.5f}, Val Loss - {:.5f}, Train Acc - {:.5f}, Val Acc - {:.5f}\n".format(
        i + 1, epochs, train_loss, val_loss, train_acc, val_acc))
    final_val_acc = val_acc
    final_train_acc = train_acc

train_end = time.time()
print("Training time: %f\n" % (train_end - train_start))
logfile.write("Training time: %f\n" % (train_end - train_start))

# Evaluate model on test dataset
test_start = time.time()

model.eval()
test_loss = 0.0
test_acc = 0.0
test_accs_dict = {i: 0.0 for i in range(1, 33)}
with torch.no_grad():
    for x, y in test_loader:
        pred = model(x)

        loss = loss_fn(pred, y)

        correct_pred = torch.isclose(
            probs(pred).argmax(dim=1), y, atol=acc_eps, rtol=0.0)
        test_acc += correct_pred.float().sum() / len(correct_pred)

        # Compute accuracy for all possible "eps" tolerance
        for k in range(1, 33):
            correct_preds = torch.isclose(
                probs(pred).argmax(dim=1), y, atol=k, rtol=0.0)
            test_accs_dict[k] += correct_preds.float().sum() / \
                len(correct_preds)

        test_loss += loss.item()

test_loss /= len(test_loader)
test_acc /= len(test_loader)
for k in range(1, 33):
    test_accs_dict[k] /= len(test_loader)
    test_accs_dict[k] = round(test_accs_dict[k].item(), 5)

print("Test Loss - {:.5f}, Test Acc - {:.5f}\n".format(
    test_loss, test_acc))
logfile.write("Test Loss - {:.5f}, Test Acc - {:.5f}\n".format(
    test_loss, test_acc))

print("Test Accuracy for 1-32 tolerance: ")
print(test_accs_dict)
logfile.write("Test Accuracy for 1-32 tolerance: \n")
logfile.write(json.dumps(test_accs_dict))

test_end = time.time()

torch.save(model, path + "traces_" +
           str(round(test_acc.item(), 5)) + '_' + activation + '.pth')

logfile.close()
