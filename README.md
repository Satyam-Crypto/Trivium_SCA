[![CC BY 4.0][cc-by-shield]][cc-by]
# Trivium-3Step-SCA

This repository contains the accompanying side channel data and source codes for the paper, **Side Channel Attacks On Stream Ciphers: A Three-Step Approach To State/Key Recovery** (published in [CHES](https://tches.iacr.org/index.php/TCHES/article/view/9485)). Our attack consists of three steps: ML, MILP and SMT experiments. The code for each is provided as a separate module.


## Description of the Attack

Our SCA attack targets the recovery of internal state bits at any particular round of the Trivium cipher using the information of erroneous Hamming weight information and keystream bits (optional) in three steps (ML + MILP + SMT). ML model predicts Hamming weight (with some noise) from the given traces, MILP model modify the obtained Hamming weight sequence to reduce the error tolerance (in our case, it reduces the error tolerance to 3 with a very high success rate) and lastly, SMT solves a set of equations (or constraints) formed from the erroneous Hamming weight sequence and keystream bits to recover the internal state bits. For the attack, first we have to tune in the tolerance of the ML and SMT models. For that, first execute ML code and note down the accuracy for varying tolerance. Thereafter run the SMT model on a simulated cipher with varying tolerance and note down the tolerance (say tl) beyond which the SMT time is infeasible even with more information (HW or keystream bits). If the ML accuracy at tolerance tl is not 100%, then use the MILP model (in between ML and SMT) to achieve 100% accuracy at tolerance, tl, with a very high probability (in our case tl = 3). In our manuscript, we have analysed the performance of each part of the framework separately, i.e., using generic traces of a 32-bit microcontroller for the ML model (script in `ML/` folder) and using simulated cipher information for MILP (script at `MILP+SMT/Trivium_MILP_PredictedHW_Correction_CHES-submission.py`) and SMT (script at `MILP+SMT/Trivium_SMT-HW-code-CHES-submission.py`). We tested each part (ML, MILP and SMT) for varying parameters and results of the same are stated in the paper. We have also tested our SMT model for Hamming distance model (script at `MILP+SMT/Trivium_SMT-HD-code-CHES-submission.py`) with varying parameters. Lastly, we computed the success probability of MILP for varying SNR by adding some Gaussian noise to the existing traces with varying standard deviations.


## Setup

Refer to the readme file for ML (`ML/README.md`) and SMT (`MILP+SMT/README.md`).


## Repository Structure

1. `ML/`: This folder contains the script for ML experiments. See readme file inside the folder for explanation.
2. `MILP+SMT/`: This folder contains the script for MILP and SMT model. See readme file inside the folder for explanation.


## How to reproduce the results stated in the paper

1. Table 3: Refer to the `ML/README.md` file to produce results of Table 3.

2. Table 4: This table is produced from the script `MILP+SMT/Trivium_MILP_PredictedHW_Correction_CHES-submission.py`. Collect `Testing Accuracy` for all tolerance from Table 3 and feed it to the array `distribution` under the Section `MILP` of the `MILP+SMT/config.ini` file. Update the `trials` variable with the number of different experiments we want to perform and `N_round` with the number of rounds for which information has to be passed. For example: In Table 3, the testing accuracies for MLP-II parameters with varying tolerances (0-7) are `[0.39266, 0.86615, 0.98234, 0.99784, 0.99965, 0.99992, 0.99999, 1.0]`. Feed it to the array `distribution` in the `MILP+SMT/config.ini` file under `MILP` section. Set `trials = 1000`, `N_round= 110` and `tolerance = 3` to produce the result corresponding to the first row of Table 4.

3. Table 5: In this table, we have analysed the performance of our SMT model for Hamming weight model in the pseudorandom phase. This table is produced from the script `MILP+SMT/Trivium_SMT-HW-code-CHES-submission.py`. Update the parameters in the Section `SMT-HW` of `MILP+SMT/config.ini` file as follows: `mc_len` - size of the microcontroller used (8/16/32); `tolerance` - error tolerance for which we have to analyse SMT model; `N_round` - number of rounds for which information has to be passed; `trials` - Number of different and independent trials that we need to perform; `init=0` as in this table we are targeting pseudo-random phase; `z_act`- 0 if we do not use keystream bit information while forming SMT instances and 1 if we are using keystream bit information for SMT instances (`z_act` = 0 for Table 5(a) and 1 for Table 5(b)); `G_pos` - positions of the internal state that are needed to be guessed (any numbers in the range `[0,state_size-1]`). For example, set `mc_len = 8`, `tolerance = 1`, `N_round = 110`, `trials= 20`, `init= 0`, `z_act = 0` and `G_pos = []` to produce the result in first row of Table 5(a).

4. Table 6: In this table, we have analysed the performance of our SMT model for Hamming weight model in the initialisation phase. The results in this table are produced from the script `MILP+SMT/Trivium_SMT-HW-code-CHES-submission.py`. Update the parameters in the Section `SMT-HW` of the `MILP+SMT/config.ini` file as follows: `mc_len` - size of the microcontroller used (8/16/32); `tolerance` - error tolerance for which we have to analyse SMT model; `N_round` - number of rounds for which information has to be passed (denoted by `#Rounds` in 3rd column of Table 6); `trials` - Number of different and independent trials that we need to perform; `init=1` as in this table we are targeting initialisation phase; `z_act = 0` as in the initialisation phase we do not have access to the keystream bits; `G_pos` - positions of the internal state that needed to be guessed (any numbers in the range `[0,state_size-1]`). For example, set `mc_len = 8`, `tolerance = 4`, `N_round = 150`, `trials= 20`, `init= 1`, `z_act = 0` and `G_pos = []` for first row of Table 6.

5. Table 7: In this table, we have analysed the performance of our SMT model for Hamming distance model. The results in the table are produced from the script `MILP+SMT/Trivium_SMT-HD-code-CHES-submission.py`. Update the parameters in the Section `SMT-HD` of the `MILP+SMT/config.ini` file as follows: `tolerance` - error tolerance for which we have to analyse SMT model; `N_round` - number of rounds for which information has to be passed; `trials` - Number of different and independent trials that we need to perform; `init=1` as in this table we are targeting initialisation phase; `z_act=0` as in the initialisation phase, keystream bits are not available; `G_pos` - positions of the internal state that needed to be guessed (any numbers in the range `[0,state_size-1]`). For example, set `tolerance = 1`, `N_round = 200`, `trials = 5`, `init =1`, `z_act = 0` and `G_pos = [65,66,67,68,69]` (state positions `s65,s66,...,s69`) for 5th entries of Table 7.

6. Table 8: In this table, we have analysed the success probability of the MILP model with respect to the different SNRs. New SNR is obtained by adding Gaussian noise to the existing traces with respect to different standard deviations (instructions for adding Gaussian noise to the existing traces can be found at `ML/README.md`). Thereafter the obtained ML accuracy with respect to different tolerance is fed to the array `distribution` in the Section `MILP` of the `MILP+SMT/config.ini` file and run the script `MILP+SMT/Trivium_MILP_PredictedHW_Correction_CHES-submission.py` to compute the success probability. 

Note that in the above description of tables, `N_round` variable in script refers to the column named `# Rounds` in the tables of the manuscript. For all entries of Table 4, `trials = 1000`; For all entries of Table 5(a) `z_act = 0` and `init = 0`; For Table 5(b), `z_act = 1` and `init = 0`; For Tables 6 and 7, `init = 1` and `z_act = 0`; For Table 8, `trials = 1000`;


# License

This work is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg
