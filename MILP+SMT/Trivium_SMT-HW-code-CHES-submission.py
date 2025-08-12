#!/usr/bin/env python
# coding: utf-8

# In[ ]:


'''
In order to simulate the SMT HW experiments for a different stream cipher, edit the code as follows:
We are assuming the stream cipher has an internal state which comprises of some registers and for each register\
one bit is incoming, one bit is outgoing and the rest bits are shifted to left/right during state update.\
Programming for other structures might change depending upon the structure.
           
Line 49-105   ----> Update the keystream, state update function (for both forward and backward direction)\
                    and encryption function in the same pattern. 

Line 119-153 ----> Update the parameter as per the specification of cipher, platform used. Also provide the \
                    value of tolerance, number of rounds etc., as per the need or update in config.ini file.

Line 173, 189, 190, 205, 219, 312, 338, 343, 358  ----> Check whether parameters are passed correctly as per keystream and \
                                                  state update functions.

Line 265-272 and 296-304 (R1,R2,R3) ---->  Update the definition of dummy variables as per the number of registers.

Line 370-373    ---->   Update as per the number of registers

Line 315-323 and 360-368  ---->   Update as per the number of register and positions of\
                        incoming bit for each register in backward/forward direction.\
                        Note that incoming bit positions for backward and forward directions are different.


In order to check the validity of the program, initially guess all bits by providing positions to G_pos. \
If it output sat, the code is okay. If it outputs unsat, it means some equations are contradictory to each other.\
Debug by removing equations one by one to spot the issue.

'''


# In[ ]:


import numpy as np
import json
import time
import random
import math
import sys
from configparser import ConfigParser

def keystream(S):  # Keystream Function
    t1 = S[65] ^ S[92]
    t2 = S[161] ^ S[176]
    t3 = S[242] ^ S[287]
    z = t1 ^ t2 ^ t3
    return z


def update_forward(S):  # State update function in forward direction
    t1 = S[65] ^ S[92] ^ S[90] & S[91] ^ S[170]
    t2 = S[161] ^ S[176] ^ S[174] & S[175] ^ S[263]
    t3 = S[242] ^ S[287] ^ S[285] & S[286] ^ S[68]

    S = [t3] + S[:92] + [t1] + S[93:176] + [t2] + S[177: 287]

    return S


def update_backward(S):  # State update function in backward direction
    t1 = S[93] ^ S[66] ^ S[91] & S[92] ^ S[171]
    t2 = S[177] ^ S[162] ^ S[175] & S[176] ^ S[264]
    t3 = S[0] ^ S[243] ^ S[286] & S[287] ^ S[69]

    S = S[1:93] + [t1] + S[94:177] + [t2] + S[178:288] + [t3]
    return S

# Encryption function ; init=1 Initialisation Phase Attack , init =0 Pseudo-random Phase Attack


def Encryption(init):
    S = [0]*288
    K = [random.randint(0, 1) for i in range(80)]  # Random Key and IV
    IV = [random.randint(0, 1) for i in range(80)]

    # Key and IV setup
    S[:80] = K[:]
    S[93:93+80] = IV[:]
    S[285] = 1
    S[286] = 1
    S[287] = 1

    if init == 1:                            # If initialisation phase then the targeted round is at the 0th round
        return S
    else:  # If pseudo-random phase attack
        # Initialisation Phase
        for i in range(4*288):
            S = update_forward(S)

        N_key = 264  # Targeted Round (Any random round)
        temp = []
        # Keystream Phase
        for i in range(N_key):

            temp.append(keystream(S))
            S = update_forward(S)
        # print(temp)
        return S


# Plan is to first simulate a cipher
# Generate original Hamming weights sequence from the cipher using an internal state S_org
# Put error randomly to the Hamming weight sequence with a given tolerance

# Recover internal state with the only knowledge of erroneous Hamming weight sequence and keystream bits (optional)


input_file = 'config.ini'
config = ConfigParser()
config.read(input_file)

state_size = int(config['SMT-HW']['state_size'])

mc_len = int(config['SMT-HW']['mc_len'])                  # Length of the micro-controller
tolerance = int(config['SMT-HW']['tolerance'])
N_round = int(config['SMT-HW']['N_round'])                     # Number of Rounds needed
init = int(config['SMT-HW']['init'])                     # 1- initialisation phase 0--pseudo-random phase
G_pos = json.loads(config.get("SMT-HW","G_pos"))                   # Put the positions for guessing of bits if needed
g = len(G_pos)               # Number of guessed bit
trials = int(config['SMT-HW']['trials'])                   # Number of different trials for the experiment
z_act = int(config['SMT-HW']['z_act'])                    # Whether to use keystream equations; 0 for no 1 for yes
multi_thread = int(config['SMT-HW']['multi_thread']) #For multi-threading Y/N = 0/1
n_thread = int(config['SMT-HW']['n_thread']) #number of threads


if init == 1:                # No keystream bits available for initialisation phase
    z_act = 0

error = 2*tolerance + 1              # Legth of the tolerance class  [-t,t]
# Number of block after the internal state is divided into block, each block of length mc_len
block_no = math.ceil(state_size/mc_len)


Err = [i for i in range(-tolerance, tolerance+1, 1)]  # Create tolerance class


# Number of bit needed to represent the max. Hamming weight i.e., mc_len
bitlen = math.floor(math.log(mc_len, 2)) + 1
runtime = [0]*trials  # Contains the SMT solution time for each trial
sat_out = 0  # Counts the number of satisfiable and correct output

if init == 0:  # For pseudo-random phase
    # Forward and Backward number of keystream, N_round is equally divided into both
    N_key_f = math.ceil(N_round/2)
    N_key_b = math.floor(N_round/2)
else:  # For initialisation phase
    N_key_f = N_round
    N_key_b = 0


print("Total number of rounds = ", N_round)
print("\nNumber of rounds in forward direction = ", N_key_f)
print("Number of rounds in backward direction = ", N_key_b)
print("State size = ", state_size, ";\t mc_len = ",
      mc_len, ";\t tolerance = ", tolerance)
print("Number of rounds = ", N_round, ";\t init = ", init, ";\t No. of Guessed bit = ", g,
      ";\t Number of trials = ", trials, ";\t keystream use yes/no 1/0 = ", z_act)
print("Multi threading used (Y/N = 1/0) = ",multi_thread)
if multi_thread == 1:
    print("Maximum number of threads to be used = ", n_thread)
    
sys.stdout.flush()

for loop in range(trials):
    # Call Encryption function to get the actual state
    S_org = Encryption(init)

    # state S consists of three register R1 [0,1, ... , 92]
    # R2  [93,94, ... ,176]   R3 [ 177,178, ... , 287]
    # size = 288-177 = 111-bit

    S = S_org[:]

    Z_f = [0]*N_key_f  # To store keybits
    Z_b = [0]*N_key_b

    # To store Hamming weight in forward and backward
    hamm_wt_f = [[0 for i in range(block_no)] for i in range(N_key_f)]
    hamm_wt_b = [[0 for i in range(block_no)] for i in range(N_key_b)]

    for i in range(N_key_b):
        S = update_backward(S)  # For backward update
        Z_b[i] = keystream(S)

        count = 0
        for l in range(block_no-1):
            # Store HW information for each block for internal state in backward direction
            for k in range(mc_len):
                hamm_wt_b[i][l] += S[count]
                count += 1

        while(count < state_size):  # Helpful when state_len is not a multiple of mc_len
            hamm_wt_b[i][-1] += S[count]
            count += 1

    S = S_org[:]
    for i in range(N_key_f):
        Z_f[i] = keystream(S)  # Store forward keystream

        count = 0
        for l in range(block_no-1):
            # Store HW information for each block for internal state in forward direction
            for k in range(mc_len):
                hamm_wt_f[i][l] += S[count]
                count += 1

        while(count < state_size):  # Helpful when state_len is not a multiple of mc_len
            hamm_wt_f[i][-1] += S[count]
            count += 1

        if i < N_key_f - 1:
            S = update_forward(S)

    cntf = 0  # Counts the number of error
    cntb = 0

    # Putting Error randomly to the obtained HW sequence
    if len(Err) != 0:
        for i in range(N_key_f):
            for j in range(block_no):
                # Put error in Hamming weight randomly
                temp = random.choice(Err)
                # such that error remains in tolerance range
                hamm_wt_f[i][j] += temp

                if temp != 0:
                    cntf += 1
                # Make sure erroneous HW of each blocks stay in [0,mc_len] as we are using modular operation
                if hamm_wt_f[i][j] >= mc_len+1:
                    hamm_wt_f[i][j] = mc_len
                if hamm_wt_f[i][j] <= -1:
                    hamm_wt_f[i][j] = 0

        for i in range(N_key_b):
            for j in range(block_no):
                # Put error in Hamming weight randomly for backward states
                temp = random.choice(Err)
                hamm_wt_b[i][j] += temp

                if temp != 0:
                    cntb += 1
                # Make sure erroneous HW of each blocks stay in [0,mc_len] as we are using modular operation
                if hamm_wt_b[i][j] >= mc_len+1:
                    hamm_wt_b[i][j] = mc_len
                if hamm_wt_b[i][j] <= -1:
                    hamm_wt_b[i][j] = 0

    # Now recover the entire state by using Z_f, Z_b, hamm_wt_f, hamm_wt_b and cipher structure

    from z3 import *
    s = Solver()

    # Define variables (each of the data structure BitVec(.,1))
    S_var_org = [BitVec('s%d' % i, 1)
                 for i in range(state_size)]  # state variables

    # Dummy variable for each registers in forward direction
    R1_f = [BitVec('r1f%d' % i, 1) for i in range(1, N_key_f, 1)]
    R2_f = [BitVec('r2f%d' % i, 1) for i in range(1, N_key_f, 1)]
    R3_f = [BitVec('r3f%d' % i, 1) for i in range(1, N_key_f, 1)]

    R1_b = [BitVec('r1b%d' % i, 1) for i in range(1, N_key_b+1, 1)]
    # Dummy variable for each registers in backward direction
    R2_b = [BitVec('r2b%d' % i, 1) for i in range(1, N_key_b+1, 1)]
    R3_b = [BitVec('r3b%d' % i, 1) for i in range(1, N_key_b+1, 1)]

   # bool_eq = [ULE(S_var_org[i],1) for i in range(len(S_var_org))] + [ULE(R1_b[i],1) for i in range(len(R1_b))] +\
    # [ULE(R2_b[i],1) for i in range(len(R2_b))] + [ULE(R3_b[i],1) for i in range(len(R3_b))] +\
    # [ULE(R1_f[i],1) for i in range(len(R1_f))] + [ULE(R2_f[i],1) for i in range(len(R2_f))] +\
    #[ULE(R3_f[i],1) for i in range(len(R3_f))]
    # s.add(bool_eq)

    S = S_var_org[:]

    if init == 1:
        for i in range(80, state_size, 1):  # If initialisation phase attack is activated
            # Then all IV-bits are known, so position 80-288 are known as per the trivium structure
            s.add(S[i] == S_org[i])

    print("The Guessed bits are", G_pos)
    sys.stdout.flush()
    for i in G_pos:  # Guessing of state bits if needed. Provide the location in the begining
        s.add(S[i] == S_org[i])

    # For keystream equations f for forward and b for backward
    Z_f_equ = [0]*N_key_f
    Z_b_equ = [0]*N_key_b

    R1_f_equ = [0]*(N_key_f-1)
    # For state update equation for each registers (forward)
    R2_f_equ = [0]*(N_key_f-1)
    R3_f_equ = [0]*(N_key_f-1)

    R1_b_equ = [0]*N_key_b
    # For state update equation for each registers (backward)
    R2_b_equ = [0]*N_key_b
    R3_b_equ = [0]*N_key_b

    hamm_wt_f_equ = [[0 for i in range(block_no)] for i in range(
        N_key_f)]  # For forward HW equations
    hamm_wt_b_equ = [[0 for i in range(block_no)] for i in range(
        N_key_b)]  # For backward HW equations

    for i in range(N_key_b):
        S = update_backward(S)  # update state normally in backward direction

        # Dummy variable is updated with the register update equations
        R1_b_equ[i] = (R1_b[i] == S[92])
        # as 92,176 and 287 are the positions of incoming bit
        R2_b_equ[i] = (R2_b[i] == S[176])
        R3_b_equ[i] = (R3_b[i] == S[287])  # during backward state update

        # State is updated with the dummy variables at the incoming position
        S[92] = R1_b[i]
        S[176] = R2_b[i]  # to avoid large degree equations
        S[287] = R3_b[i]

        count = 0
        for l in range(block_no-1):
            for k in range(mc_len):
                # Form HW equations by changing the variables format
                hamm_wt_b_equ[i][l] += ZeroExt(bitlen-1, S[count])
                # so that 2^(bitlen) modulus operation can be performed
                count += 1

        while(count < state_size):  # Helpful when state_len is not a multiple of mc_len
            hamm_wt_b_equ[i][-1] += ZeroExt(bitlen-1, S[count])
            count += 1

        # Form keystream equation and equate it to known values
        Z_b_equ[i] = (keystream(S) == Z_b[i])

    S = S_var_org[:]
    for i in range(N_key_f):
        # keystream equation in forward direction and equate it to the knonw values
        Z_f_equ[i] = (keystream(S) == Z_f[i])

        count = 0
        for l in range(block_no-1):
            for k in range(mc_len):
                # HW equations in the forward directions
                hamm_wt_f_equ[i][l] += ZeroExt(bitlen-1, S[count])
                count += 1

        while(count < state_size):  # Helpful when state_len is not a multiple of mc_len
            hamm_wt_f_equ[i][-1] += ZeroExt(bitlen-1, S[count])
            count += 1

        # update
        if i < N_key_f-1:
            S = update_forward(S)
            # Dummy variable is updated with the register update equations
            R1_f_equ[i] = (R1_f[i] == S[0])
            # 0,93,177 are positions for incoming bits for forward state update
            R2_f_equ[i] = (R2_f[i] == S[93])
            R3_f_equ[i] = (R3_f[i] == S[177])

            S[0] = R1_f[i]
            # State is updated with the dummy variables at the update positions
            S[93] = R2_f[i]
            S[177] = R3_f[i]

    if z_act == 1:  # To include keystream equations
        Equ = Z_f_equ + R1_f_equ + R2_f_equ + R3_f_equ + Z_b_equ + R1_b_equ + R2_b_equ + R3_b_equ
    else:
        Equ = R1_f_equ + R2_f_equ + R3_f_equ + R1_b_equ + R2_b_equ + R3_b_equ

    s.add(Equ)  # Fed all the equations above to the solver
    print("Error Range", Err)
    print("tolerance", tolerance)

    for l in range(block_no):  # For feeding erroneous HW data
        for i in range(N_key_f):
            if hamm_wt_f[i][l] - tolerance >= 0:
                # HW_equ >= HW_predicted - tolerance
                s.add(UGE(hamm_wt_f_equ[i][l], hamm_wt_f[i][l]-tolerance))
            else:
                # To make sure it is not negative
                s.add(UGE(hamm_wt_f_equ[i][l], 0))

            if hamm_wt_f[i][l] + tolerance <= (mc_len):
                # HW_equ <= HW_predicted + tolerance
                s.add(ULE(hamm_wt_f_equ[i][l], hamm_wt_f[i][l]+tolerance))
            else:
                # To make sure it is not greater than mc_len
                s.add(ULE(hamm_wt_f_equ[i][l], mc_len))
            # As for modular form the value will change if it is outside the range [0,32]
            # For example -1 will be treated as 31 and so on

        for i in range(N_key_b):
            if hamm_wt_b[i][l] - tolerance >= 0:
                # HW_equ >= HW_predicted - tolerance
                s.add(UGE(hamm_wt_b_equ[i][l], hamm_wt_b[i][l]-tolerance))
            else:
                s.add(UGE(hamm_wt_b_equ[i][l], 0))

            if hamm_wt_b[i][l] + tolerance <= (mc_len):
                # HW_equ <= HW_predicted + tolerance
                s.add(ULE(hamm_wt_b_equ[i][l], hamm_wt_b[i][l]+tolerance))
            else:
                s.add(ULE(hamm_wt_b_equ[i][l], mc_len))

    if multi_thread == 1:
    	set_param("parallel.enable", True)
    	set_option("parallel.threads.max", n_thread)

    start = time.time()
    temp = s.check()  # Solve SMT instances
    end = time.time()

    if temp == sat:
        print(temp)
        soln = s.model()
    else:
        print("###################################unsat###################################################")
        print(temp)
        print(S_org)
        continue
    print("loop", loop)

    print("runtime = ", end - start)  # If it is not unsat
    runtime[loop] = end - start
    out = [0]*state_size
    for i in range(state_size):
        # Extract the values of state variables from the output
        out[i] = soln[S_var_org[i]]
    # print(out)
    # print(S_org)
    if S_org == out:  # Check if it matches with the original state
        print("**************************************matched***************************************")
        sat_out += 1
    else:
        print("############################not matched#######################33#######################")
        print(S_org)
        print(out)
    sys.stdout.flush()

runtime = np.array(runtime)
print("\n\n Mean =  ")
print(runtime.mean())
print("\n Std = ")
print(runtime.std())
print("\n")
sys.stdout.flush()


# In[ ]:




