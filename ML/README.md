# ML to Predict Classes from Traces
![Python 3.8](https://img.shields.io/badge/python-3.8-green.svg)
![PyTorch 1.8.1](https://img.shields.io/badge/pytorch-1.8.1-green.svg)

This folder contains the code to run the Machine Learning step of the key recovery attack on TRIVIUM. The ML models and data are for the Hamming Weight (HW) leakage model.

## Setup

1. *(Optional but recommended)* Create a virtual environment with conda: `conda create -n trivium_sca python=3.8`
2. *(Optional but recommended)* Activate the virtual environment: `conda activate trivium_sca`
3. Install the required packages using pip: `pip install -r requirements.txt`

Alternatively, use the `conda_install.sh` script to create a `conda` environment and install the required packages.

## Repository Structure

1. `run_traces.py`: Script to train MLP model on 32-bit microcontroller traces.
2. `run_traces_optuna.py`: Script to identify optimal hyperparameters using Optuna.
3. `run_traces_noisy.py`: Script to train MLP on 32-bit microcontroller traces with additive white Gaussian noise to simulate lower SNR.
4. `run_traces_pretrained.py`: Script to load pretrained model and run prediction on 32-bit microcontroller traces.
5. `datagen.py`: Utility to process raw data for training.
6. `get_snr.py`: Utility to compute SNR.
7. `config.ini`: Config file to set hyper parameters and other variables for model training.
8. `data/`: Contains the 32-bit microcontroller traces raw data.
9. `results/manual/`: Contains the log files, pretrained models, and config files for the results in the paper achieved using manual experimentation.
10. `results/optuna/`: Contains the log files, pretrained models, and config files for the results in the paper achieved using Optuna.
11. `results/noisy/`: Contains the log files, pretrained models, and config files for the results in the paper for simulating lower SNR.

## Usage

1. Unzip all zip files in `data/` i.e `cd data && unzip \*.zip`.

### Train ML Model

1. Update `config.ini` with required hyper parameters and variables.
2. Run `python run_traces.py`, `python run_traces_optuna.py`, or `python run_traces_noisy.py` for manual training, to identify optimal hyperparameters using Optuna under given constraints, or for manual training with additive white Gaussian noise.

The trained models and log files can be found in `traces_models`/`traces_model_opt`/`traces_models_noisy` and `trace_logs.log`/`trace_logs_opt.log`/`trace_logs_noisy.log` for the manual training, Optuna, and low SNR (noisy) experiments respectively.

### Load Pretrained Model

1. Run `python run_traces_pretrained.py` by passing the pretrained model as an argument i.e. `python run_traces_pretrained.py -f results/manual/traces_models/traces_0.3933_ReLU.pth`

```
$ python run_traces_pretrained.py -h
```
```
usage: run_traces_pretrained.py [-h] -f FILE

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Path of saved model (.pth)
```

## Note

In case of any errors while installing `pytorch`, you may have to change the version of `pytorch` or install the CPU only variant. Please refer to the [documentation](https://pytorch.org/get-started/locally/) for a detailed description on the various installation options.
