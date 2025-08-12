import argparse

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from datagen import *

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# PyTorch dataset class
class TracesDataset(Dataset):

    def __init__(self, x, y):
        self.x = torch.from_numpy(x).float().to(device=device)
        self.y = torch.from_numpy(y).to(device=device)

    def __len__(self):
        return len(self.x)

    def __getitem__(self, item):
        return self.x[item], self.y[item]


parser = argparse.ArgumentParser()
parser.add_argument(
    "-f", "--file", help="Path of saved model (.pth)", required=True)
args = parser.parse_args()
model_path = args.file

# Load dataset
X, y = load_full_data()

# Create PyTorch dataset and dataloader
test_set = TracesDataset(X, y)
test_loader = DataLoader(
    dataset=test_set, batch_size=64, shuffle=False)

# Load pretrained model
model = torch.load(model_path, map_location=device)
model.eval()

probs = nn.Softmax(dim=1)

test_acc = 0.0
test_accs_dict = {i: 0.0 for i in range(1, 33)}

# Run prediction
with torch.no_grad():
    for x, y in test_loader:
        pred = model(x)

        correct_pred = torch.isclose(
            probs(pred).argmax(dim=1), y, atol=0, rtol=0.0)
        test_acc += correct_pred.float().sum() / len(correct_pred)

        for k in range(1, 33):
            correct_preds = torch.isclose(
                probs(pred).argmax(dim=1), y, atol=k, rtol=0.0)
            test_accs_dict[k] += correct_preds.float().sum() / \
                len(correct_preds)

test_acc /= len(test_loader)
for k in range(1, 33):
    test_accs_dict[k] /= len(test_loader)
    test_accs_dict[k] = round(test_accs_dict[k].item(), 5)

print("Test Acc - {:.5f}\n".format(test_acc))

print("Test Accuracy for 1-32 tolerance: ")
print(test_accs_dict)
