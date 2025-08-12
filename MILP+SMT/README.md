This folder contains the scripts of SMT and MILP model on TRIVIUM Cipher. For SMT model, we have considered Hamming weight and Hamming distance model. 

## Software Used
1. [Z3-Sovler](https://github.com/Z3Prover/z3)
2. [Gurobi](https://www.gurobi.com/)


## Setup

1. Create a virtual environment with conda: `conda create -n trivium_sca python=3.8`
2. Activate the new environment: `conda activate trivium_sca`
3. Install the required python packages using pip: `pip install -r requirements.txt`
4. Add [Gurobi](https://www.gurobi.com/documentation/9.5/quickstart_linux/cs_anaconda_and_grb_conda_.html) channels as follows: `conda config --add channels https://conda.anaconda.org/gurobi`
5. Install Gurobi using conda: `conda install gurobi`
6. For Gurobi software, obtain the Academic license from the [website](https://www.gurobi.com/downloads/end-user-license-agreement-academic/)
7. Activate license using the command: `grbgetkey <license-number>`


## File Structure

1. `Trivium_MILP_PredictedHW_Correction_CHES-submission.py`: Script for MILP model on TRIVIUM cipher for correction of ML predicted Hamming weight sequence. In this experiment, we simulate a Trivium cipher with a random key/IV, generate a sequence of original HW sequence and inject noise as per the distribution of ML output. After that, we form MILP instances to reduce the error tolerance of erroneous HW sequence. It relates to Section 4.3.2 of the manuscript and reproduces the results of Tables 4 and 8. The input parameters are defined in the Section `MILP` inside the `config.ini` file.

2. `Trivium_SMT-HW-code-CHES-submission.py`: Script to recover internal state bits from erroneous Hamming weight and keystream bits (optional) information. First, we simulated a Trivium cipher with a random key/IV; then we injected noise randomly to the original Hamming weight(HW) sequence within the given tolerance class. After that, we formed SMT instances with the help of the erroneous HW sequence and solved it to recover the internal state bits. It relates to Section 5.1 of the manuscript and reproduces the results of Tables 5 and 6. The input parameters are passed through the `config.ini` file (Section `SMT-HW`).

3. `Trivium_SMT-HD-code-CHES-submission.py`: Script to recover internal state bits from erroneous Hamming distance and keystream bits (optional) information. It works by simulating a Trivium cipher with a random key/IV and then we inject noise randomly within the given tolerance class to the original Hamming distance (HD) sequence. After that, we formed SMT instances with the help of the erroneous HD sequence and solved it to recover the internal state bits. It relates to Section 5.2 of the manuscript and reproduces the results of Table 7. The input parameters are defined under the section `SMT-HD` inside the `config.ini` file.

4. `requirements.txt`: It contains the python packages required for compilation of the above three scripts.

5. `config.ini`: It contains the input parameters for all of the above three python scripts under different sections.


Note that for some parameters, the solution time for the above scripts might go beyond 24-48 hours. Additionally, for a fixed parameter set, the solution time could be higher from the reported mean time as the standard deviation is quite high, especially for `Trivium_SMT-HD-code-CHES-submission.py`. For the HW model, the solution time becomes higher after tolerance 3 in the pseudo-random phase, whereas for the HD model, solution time goes higher after tolerance 3 in the initialisation phase. Refer to the tables in the manuscript to get an estimate of the solution time. 


## Usage
Update `config.ini` with the the input parameters in the corresponding section (`MILP` for MILP model; `SMT-HW` for SMT model on Hamming weight; `SMT-HD` for SMT model on Hamming distance) and compile using `python3 filename.py`.


