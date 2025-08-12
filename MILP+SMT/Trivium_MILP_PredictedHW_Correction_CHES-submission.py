#!/usr/bin/env python
# coding: utf-8

# In[ ]:


'''
MILP modelling for a general stream cipher.
Let us assume that the stream cipher consists of registers connected serially.

First go through the Section 4.3.2 in the manuscript to generate all constraints I, II and III.
Then edit the code as follows: 

Line 53-95  ----> Update with state update and encryption function of the cipher.

Update the input parameters in config.ini file as per the cipher structure and microcontroller width.

                                   
Line 139,159   ----> Verify that parameters are passed in the format of defined function.


Line 236-243   ----> Update the variables as per the number of constraint obtained using Section 4.3.2.

Line 254-64   ----> Update with the number of incoming and outgoing bits of an internal state during update.

Line 267-300   ----> Put the pair of blocks for which Constraint III holds (see Section 4.3.2).

">>" is used for implication in Gurobi.


'''


# In[ ]:


#####################################All function definition##################################################
import numpy as np
import json
import time
import random
import math
import gurobipy as gp
from gurobipy import GRB
from configparser import ConfigParser
import sys

def keystream(S):
    t1 = S[65] ^ S[92]
    t2 = S[161] ^ S[176]
    t3 = S[242] ^ S[287]
    z = t1 ^ t2 ^ t3
    return z


def update_forward(S):
    t1 = S[65] ^ S[92] ^ S[90] & S[91] ^ S[170]
    t2 = S[161] ^ S[176] ^ S[174] & S[175] ^ S[263]
    t3 = S[242] ^ S[287] ^ S[285] & S[286] ^ S[68]

    S = [t3] + S[:92] + [t1] + S[93:176] + [t2] + S[177: 287]

    return S


def Encryption():
    S = [0]*288
    K = [random.randint(0, 1) for i in range(80)]
    IV = [random.randint(0, 1) for i in range(80)]

    # Key and IV setup
    S[:80] = K[:]
    S[93:93+80] = IV[:]
    S[285] = 1
    S[286] = 1
    S[287] = 1

    # Initialisation Phase
    for i in range(4*288):
        S = update_forward(S)

    N_round = 264                   # any random rounds in the pseudo random phase
    temp = []
    # Keystream Phase
    for i in range(N_round):

        temp.append(keystream(S))
        S = update_forward(S)
    # print(temp)
    return S


# Plan is to simulate trivium cipher with a random key and IV
# Generate and store keystream bits and Hamming weight information for each round

# Put error in the Hamming weight randomly such that the tolerance class follows the distribution shown in the paper
# for example, see Table 3 in paper, refer to the second row (MLP-II)
# 0.39266 of HWs are with tolerance 0; 0.86615 of HWs are under tolerance 1 i.e. error is either 0,1 or -1

# Form MILP instances using erroneous Hamming weight
# For a given tolerance, solve MILP instance.

input_file = 'config.ini'
config = ConfigParser()
config.read(input_file)

state_size = int(config['MILP']['state_size'])

N_round = int(config['MILP']['N_round'])  # Number of Rounds
trials = int(config['MILP']['trials'])  # Number of Trials
tolerance = int(config['MILP']['tolerance'])  # Error tolerance class


mc_len = int(config['MILP']['mc_len'])  # Size of the microcontroller used
# diff: contains the number of incoming for each blocks starting from B_0
# diff: update as per the size of block, currently it is adjusted as per 32-bit microcontroller model
diff = json.loads(config.get("MILP","diff"))
# Number of incoming == Number of outgoing bits for each block in case of Trivium


block_no = math.ceil(state_size/mc_len)  # Number of blocks

# In Trivium state_size is a multiple of mc_len = 8/16/32.

distribution = json.loads(config.get("MILP","distribution"))  # MLP-II in Table 3 in the manuscript
# Distribution contains the accuracy of ML with respect to different tolerance as shown in Table 3 in the paper.
# Put value accordingly: distribution = Accuracy([tolerance 0, tolerance 1, tolerance 2, ......, tolerance 7])

cnt_abn = 0  # For count of unsuccessful experiment
runtime = [0]*trials  # To store Gurobi runtime
print("State size  = ", state_size, ";\t Number of rounds = ", N_round, ";\t Number of trials = ", trials,)
print("Error tolerance = ", tolerance, ";\t Microcontroller width = ", mc_len,";\t Number of blocks = ",block_no)
print("Number of incoming bits to each blocks, starting from B0 = ", diff)
print("Probability distribution of Noise of ML output (in the format [tolerance 0; tolerance 1; ....]) = ", distribution)
sys.stdout.flush()
for loop in range(trials):
   ############################################Program to generate original Hamming Weight###################################

    S_org = Encryption()

    # state S consists of three register R1 [0,1, ... , 92]
    # R2  [93,94, ... ,176]   R3 [ 177,178, ... , 287]
    # size = 288-177 = 111-bit

    S = S_org[:]

    hamm_wt = [[0 for i in range(block_no)]
               for i in range(N_round)]  # For Hamming weight

    # Code to generate and store original Hamming weight
    for i in range(N_round):
        count = 0
        for l in range(block_no):
            for k in range(mc_len):
                hamm_wt[i][l] += S[count]
                count += 1

        if i < N_round - 1:
            S = update_forward(S)  # State update

    #####################Program to inject error randomly such that it follows the distribution####################

    # To store the erroneous HW
    hamm_wt_predict = [[hamm_wt[i][j]
                        for j in range(block_no)] for i in range(N_round)]

    N = N_round*block_no  # Total number of blocks in N_round rounds
    # temp[i] contains the number of HW classes needed in ith tolerance class
    temp = [math.floor(N*i) for i in distribution]

    # Now C[i] will contain number of HW class that should differ from the original HW class by i
    C = [round(temp[0])] + [round(temp[i] - temp[i-1])
                            for i in range(1, len(temp))]
    print("Trial No. = ", loop, "\nAs per the distribution:")
    for i in range(len(C)):
        print("Number of classes with error/tolerance equal to ",
              i, " are ", C[i])

    avl = [i for i in range(N)]  # Stores all positions of the blocks

    # predict_pos[i][j] will contains C[j] positions (selected randomly)
    # that should be injected with error i
    predict_pos = [[0 for i in range(C[j])] for j in range(len(C))]

    for c in range(len(C)):
        cnt = 0
        # conditions to make sure it follows the distribution in C
        while cnt < C[c] and len(avl) != 0:
            # random selection for positions from avl
            temp = random.choice(avl)
            predict_pos[c][cnt] = temp  # stores the positions in predict_pos
            avl.remove(temp)  # remove the chosen element from avl
            cnt += 1
        if len(avl) == 0 and c == len(C)-1:
            predict_pos[c] = []

    #####################code to create predict hamming weight#########
    for i in range(len(predict_pos)):
        for j in predict_pos[i]:
            # Error being injected
            hamm_wt_predict[j//block_no][j %
                                         block_no] += random.choice([-i, i])

    print("Positions where errors are outside the tolerance ",len(distribution)-1, " are ", avl)
    # If any positions in avl is left, put an error randomly upto 16 as error beyond +-16 is unlikely
    for i in avl:
        temp = random.choice([j for j in range(len(distribution), 16, 1)])
        hamm_wt_predict[i//block_no][i %
                                     block_no] += random.choice([-temp, temp])

    ################Program for verification if error is injected according to the C or not####################
    check = [[hamm_wt[i][j] - hamm_wt_predict[i][j]
              for j in range(block_no)] for i in range(N_round)]
    for i in range(len(predict_pos)):
        for j in predict_pos[i]:
            if check[j//block_no][j % block_no] not in [-i, i]:
                print(i, j, hamm_wt[j//block_no][j %
                      block_no], hamm_wt_predict[j//9][j % 9])

    #print("Number of rounds = ",N_round)
    # print("#############################################Original Hamming Weight################################")
    # print(hamm_wt)
    ##print("\n\n&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&Predicted Hamming Weight&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    # print(hamm_wt_predict)
    sys.stdout.flush()
    # MILP program to correct predicted HW hamm_wt_predict
    predict = [[hamm_wt_predict[i][j]
                for j in range(block_no)] for i in range(N_round)]

    var_r = N_round
    var_c = block_no

    ##################Gurobi Modelling Starts#####################################
    model = gp.Model()

    x = model.addVars(var_r, var_c, lb=-1*GRB.INFINITY,
                      vtype=GRB.INTEGER, name="x")
    y = model.addVars(var_r, var_c, lb=-1*GRB.INFINITY,
                      vtype=GRB.INTEGER, name="y")  # MILP variables
    z = model.addVars(var_r, var_c, lb=-1*GRB.INFINITY,
                      vtype=GRB.INTEGER, name="z")
    w = model.addVars(var_r-1, var_c, vtype=GRB.BINARY, name="w")
    v = model.addVars(var_r-1, var_c, vtype=GRB.BINARY, name="v")

    # Adding objective function z[i] = |x[i]-predict[i]| as follows:
    model.setObjective(gp.quicksum(z[i, j] for i in range(
        var_r) for j in range(var_c)), GRB.MINIMIZE)
    model.addConstrs(z[i, j] == gp.abs_(y[i, j]) for i in range(var_r)
                     for j in range(var_c))  # For absolute values
    model.addConstrs(y[i, j] == (x[i, j]-predict[i][j])
                     for i in range(var_r) for j in range(var_c))

    # Constraint I: 3 incoming bits and 3 outgoing bits for the whole state in Trivium
    for i in range(1, var_r):
        model.addConstr(((gp.quicksum(x[i, j] for j in range(
            var_c))) - (gp.quicksum(x[i-1, j] for j in range(var_c)))) <= 3)
        model.addConstr(((gp.quicksum(x[i, j] for j in range(
            var_c))) - (gp.quicksum(x[i-1, j] for j in range(var_c)))) >= -3)

    # Constraint II: Incoming and outgoint for each block
    for j in range(var_c):
        # constraint |x[i] - x[i+1]| <= diff
        model.addConstrs(x[i, j]-x[i+1, j] <= diff[j] for i in range(var_r-1))
        model.addConstrs(x[i, j]-x[i+1, j] >= -diff[j] for i in range(var_r-1))

    # Constraint III: Case1: Shifting of Hamming weight after mc_len rounds
    for i in range(var_r-mc_len):
        # See paper for this array or block selection
        for col in [[0, 1], [3, 4], [6, 7], [7, 8]]:
            model.addConstr((x[i, col[0]]-x[i+mc_len, col[1]]) == 0)

    # Constraint III: Case2: Incoming and outgoing bit of block affects its next block
    for i in range(var_r-1):
        for col in [[0, 1], [3, 4], [6, 7], [7, 8]]:
            model.addConstr((w[i, col[0]] == 1) >> (
                (x[i, col[1]] - x[i+1, col[1]]) >= 0))
            model.addConstr((w[i, col[0]] == 0) >> (
                (x[i, col[0]] - x[i+1, col[0]]) >= 0))  # negation == -1
            model.addConstr((v[i, col[0]] == 1) >> (
                (x[i, col[1]] - x[i+1, col[1]]) <= 0))
            model.addConstr((v[i, col[0]] == 0) >> (
                (x[i, col[0]] - x[i+1, col[0]]) <= 0))  # negation == 1
        for col in [[1, 2], [4, 5]]:
            model.addConstr((w[i, col[0]] == 1) >> (
                (x[i, col[1]] - x[i+1, col[1]]) >= -1))
            model.addConstr((w[i, col[0]] == 0) >> (
                (x[i, col[0]] - x[i+1, col[0]]) >= 0))  # negation == -1
            model.addConstr((v[i, col[0]] == 1) >> (
                (x[i, col[1]] - x[i+1, col[1]]) <= 1))
            model.addConstr((v[i, col[0]] == 0) >> (
                (x[i, col[0]] - x[i+1, col[0]]) <= 0))  # negation == 1
        for col in [[2, 3], [5, 6]]:
            model.addConstr((w[i, col[0]] == 1) >> (
                (x[i, col[1]] - x[i+1, col[1]]) >= 0))
            model.addConstr((w[i, col[0]] == 0) >> (
                (x[i, col[0]] - x[i+1, col[0]]) >= -1))  # negation == -2
            model.addConstr((v[i, col[0]] == 1) >> (
                (x[i, col[1]] - x[i+1, col[1]]) <= 0))
            model.addConstr((v[i, col[0]] == 0) >> (
                (x[i, col[0]] - x[i+1, col[0]]) <= 1))  # negation ==2

    model.Params.outputflag = 0
    model.Params.Threads = 1

    start = time.time()
    model.optimize()  # Solve MILP instance
    temp = model.x
    end = time.time() - start

    runtime[loop] = end

    temp = temp[:len(x)]  # Extract the new HWs value from the output
    HW_out = [[0 for i in range(block_no)] for j in range(N_round)]

    for i in range(len(x)):
        # convert all to an integer sometimes a fractional values comes out
        temp[i] = int(temp[i])

    for i in range(len(temp)):
        # Arrange the obtained HW in double array form
        HW_out[i//block_no][i % block_no] = temp[i]

    # Now check the tolerance of the obtained HWs with the original HWs
    flag = 0
    count = [0]*32
    cnt = 0
    for i in range(N_round):
        for j in range(block_no):
            A = abs(HW_out[i][j] - hamm_wt[i][j])
            count[A] += 1
            if A > tolerance:
                #print("Output outside the given tolerance", A)
                cnt += 1
                flag = 1
    if flag == 1:
        cnt_abn += 1  # Counts the unsuccessful experiment
    print("################################Output HW sequence################################")
    for i in range(len(count)):
        if i < 6:
            # Display the distribution of the output HWs
            print("tolerance class ", i, " Number of HWs ", count[i])
        if i >= 6 and count[i] != 0:
            print("tolerance class ", i, " Number of HWs ", count[i])

    print("Gurobi Time = ", end)
    print("\n\n\n")

print("successrate", ((trials-cnt_abn)/trials)*100,"%")

runtime = np.array(runtime)
print("Number of rounds = ",N_round)
print("Mean =", runtime.mean(),"\t Standard Deviation =", runtime.std())
sys.stdout.flush()

# In[ ]:





# In[ ]:




