#!/usr/bin/env python
# coding: utf-8

# In[ ]:


'''
In order to simulate the SMT HD experiments for a different stream cipher, edit the code in the next cell as follows:
We are assuming the stream cipher has an internal state which comprises of some registers and for each register\
one bit is incoming, one bit is outgoing and the rest bits are shifted to left/right during state update.\
Programming for other structures might change depending upon the structure.
           
Line 49-106  ----> Update the keystream, state update (forward and backward) and\
                    encryption function in the same pattern.

Line 127-163  ----> Update the cipher specifications and other parameters, e.g., \
                    tolerance, number of rounds etc., as per needed. Or update in the config.ini file.

Line 179,199,201,209,214,296,315,320,326    ----> Verify whether the parameters \
                                                    are passed as per the function definitions.

Line 249-260, 280-288 ----> Update the definitions as per the number of registers.

Line 298-307, 328-334 ----> Provide with the incoming bit positions for all registers \
                            in both forward and backward directions.

Line 340-345 ----> Pass equations as per the number of registers.



In order to check the validity of the program, initially guess all bits by providing positions to G_pos. \
If it output sat, the code is okay. If it outputs unsat, it means some equations are contradictory to each other.\
Debug by removing equation one by one to spot the issue.

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

        # Targeted Round (Any random round) if the pseudo-random phase
        N_key = 264
        temp = []
        # Keystream Phase
        for i in range(N_key):

            temp.append(keystream(S))
            S = update_forward(S)
        # print(temp)
        return S


# Plan is to first simulate a cipher
# Generate original Hamming distance sequence from the cipher using an internal state S_org
# Put error randomly to the Hamming distance sequence with a given tolerance

# Recover internal state with the only knowledge of erroneous Hamming distance sequence and keystream bits (optional)


# Trivium Encryption
# Specificaton
# 288-bit internal state
# R1 93-bit  R2 84-bit R3 111-bit
# Key 80-bit
# IV 80-bit

input_file = 'config.ini'
config = ConfigParser()
config.read(input_file)

state_size = int(config['SMT-HD']['state_size'])
N_round = int(config['SMT-HD']['N_round'])  # Number of Rounds needed
G_pos = json.loads(config.get("SMT-HD","G_pos"))  # Provide guess positions if needed

init = int(config['SMT-HD']['init'])  # 0-pseudorandom phase ; 1- initialisation phase
z_act = int(config['SMT-HD']['z_act'])  # whether to use keystream equation or not
multi_thread = int(config['SMT-HD']['multi_thread']) #For multi-threading Y/N = 0/1
n_thread = int(config['SMT-HD']['n_thread']) #number of threads

if init == 1:  # No keystream equations in initialisation phase
    z_act = 0

tolerance = int(config['SMT-HD']['tolerance'])  # Error Tolerance
trials = int(config['SMT-HD']['trials'])  # Number of trials needed

error = 2*tolerance + 1  # Length of the tolerance class  [-t,t]
guess = len(G_pos)

print("Number of Guessed Bit", guess)

Err = [i for i in range(-tolerance, tolerance+1, 1)]

print("Error range = ", Err)

# Define bitlen as the number of bits needed to represents maximum HD
# We will work in 2^(bitlen) modulus
bitlen = math.floor(math.log(state_size, 2))+1

runtime = [0]*trials  # Stores the SMT time for each trial
sat_out = 0  # Counts the number of correct output out of all trials

if init == 0:  # Divide N_round equally for forward and backward round in pseudorandom phase
    N_key_f = math.ceil(N_round/2)
    N_key_b = math.floor(N_round/2)
else:  # Only forward rounds for initialisation phase
    N_key_f = N_round
    N_key_b = 0

print("Total number of rounds = ", N_round)
print("Number of rounds in forward directions = ", N_key_f,
      ";\t Number of rounds in backward directions = ", N_key_b)
      
print("State size =", state_size, ";\ttolerance =", tolerance)
print("N_round =", N_round, ";\t init =", init, ";\t No. of Guessed bit = ", guess,
      ";\t Number of trials = ", trials, ";\t keystream use (Y/N = 1/0) =", z_act)
print("Multi threading used (Y/N = 1/0) = ",multi_thread)
if multi_thread == 1:
    print("Maximum number of threads to be used = ", n_thread)
    
sys.stdout.flush()

for loop in range(trials):
    S_org = Encryption(init)

    # state S consists of three register R1 [0,1, ... , 92]
    # R2  [93,94, ... ,176]   R3 [ 177,178, ... , 287]
    # size = 93, 176-92 = 84 and 288-177 = 111-bit

    S = S_org[:]

    Z_f = [0]*N_key_f
    Z_b = [0]*N_key_b

    # Array to store the HD of all consecutive internal states in forward directions
    hamm_dist_f = [0 for i in range(N_key_f-1)]

    # Array to store the HD of all consecutive internal states in backward directions
    hamm_dist_b = [0 for i in range(N_key_b)]

    # Information on keystream and HD/Full in backward direction
    for i in range(N_key_b):
        temp1 = S[:]
        S = update_backward(S)
        temp2 = S[:]
        Z_b[i] = keystream(S)

        # Storing the HD of internal states in backward direction
        for l in range(state_size):
            hamm_dist_b[i] += (temp1[l] ^ temp2[l])

    S = S_org[:]
    for i in range(N_key_f):
        Z_f[i] = keystream(S)  # Keystream bits information for forward rounds

        temp1 = S[:]

        if i < N_key_f - 1:
            S = update_forward(S)
            temp2 = S[:]

            for l in range(state_size):
                # HD information for forward rounds
                hamm_dist_f[i] += (temp1[l] ^ temp2[l])

    # Putting error within tolerance limit randomly.
    if len(Err) != 0:
        for i in range(N_key_f-1):
            temp = random.choice(Err)
            hamm_dist_f[i] += temp

            # To ensure that after putting error it does not goes out of the class [0,state_size]
            if hamm_dist_f[i] >= state_size+1:
                hamm_dist_f[i] = state_size
            if hamm_dist_f[i] <= -1:
                hamm_dist_f[i] = 0

        for i in range(N_key_b):
            temp = random.choice(Err)
            hamm_dist_b[i] += temp

            if hamm_dist_b[i] >= state_size+1:
                hamm_dist_b[i] = state_size
            if hamm_dist_b[i] <= -1:
                hamm_dist_b[i] = 0

    from z3 import *
    from z3 import Solver
    m = Solver()

    S_var_org = [BitVec('s%d' % i, bitlen)
                 for i in range(state_size)]  # State variables

    R1_f = [BitVec('r1f%d' % i, bitlen) for i in range(1, N_key_f, 1)]
    # Dummy variables for registers for forward direction
    R2_f = [BitVec('r2f%d' % i, bitlen) for i in range(1, N_key_f, 1)]
    R3_f = [BitVec('r3f%d' % i, bitlen) for i in range(1, N_key_f, 1)]

    R1_b = [BitVec('r1b%d' % i, bitlen) for i in range(1, N_key_b+1, 1)]
    # Dummy variables for registers for backward direction
    R2_b = [BitVec('r2b%d' % i, bitlen) for i in range(1, N_key_b+1, 1)]
    R3_b = [BitVec('r3b%d' % i, bitlen) for i in range(1, N_key_b+1, 1)]

    # All variables are less than or equal 1
    bool_eq = [ULE(S_var_org[i], 1) for i in range(len(S_var_org))] + [ULE(R1_b[i], 1) for i in range(len(R1_b))] +        [ULE(R2_b[i], 1) for i in range(len(R2_b))] + [ULE(R3_b[i], 1) for i in range(len(R3_b))] +        [ULE(R1_f[i], 1) for i in range(len(R1_f))] + [ULE(R2_f[i], 1) for i in range(len(R2_f))] +        [ULE(R3_f[i], 1) for i in range(len(R3_f))]

    m.add(bool_eq)  # Fed bool_eq to the solver

    S = S_var_org[:]

    if init == 1:
        # In initialisation phase, IV is known
        for i in range(80, state_size, 1):
            # Internal state contains IV or some known string after first 80-bit at round 0 in initialisation phase
            m.add(S[i] == S_org[i])

    print("Guessed position", G_pos) # For guessing if needed
    sys.stdout.flush()
    for i in G_pos:
        m.add(S[i] == S_org[i])

    Z_f_equ = [0]*N_key_f
    Z_b_equ = [0]*N_key_b

    R1_f_equ = [0]*(N_key_f-1)
    # For dummy variables equations in forward directions
    R2_f_equ = [0]*(N_key_f-1)
    R3_f_equ = [0]*(N_key_f-1)

    R1_b_equ = [0]*N_key_b
    # For dummy variables equations in backward directions
    R2_b_equ = [0]*N_key_b
    R3_b_equ = [0]*N_key_b

    # Array to store the HD/Full equations
    hamm_dist_f_equ = [0 for i in range(N_key_f-1)]
    hamm_dist_b_equ = [0 for i in range(N_key_b)]

    for i in range(N_key_b):
        temp1 = S[:]
        S = update_backward(S)

        R1_b_equ[i] = (R1_b[i] == S[92])
        # Equate dummy variables with the state update function
        R2_b_equ[i] = (R2_b[i] == S[176])
        # 92,176,287 are the incoming bits position during backward update
        R3_b_equ[i] = (R3_b[i] == S[287])

        S[92] = R1_b[i]
        # State is updated with the dummy variables to avoid large degree equations
        S[176] = R2_b[i]
        S[287] = R3_b[i]
        temp2 = S[:]

        for l in range(state_size):
            # Hamming distance equation
            hamm_dist_b_equ[i] += (temp1[l] ^ temp2[l])

        # Keystream equation for backward rounds
        Z_b_equ[i] = (keystream(S) == Z_b[i])

    S = S_var_org[:]
    for i in range(N_key_f):
        # Keystream equation for forward rounds
        Z_f_equ[i] = (keystream(S) == Z_f[i])

        temp1 = S[:]

        # update
        if i < N_key_f-1:
            S = update_forward(S)
            # 0,93,177 are the positions for incoming bit during forward update
            R1_f_equ[i] = (R1_f[i] == S[0])
            R2_f_equ[i] = (R2_f[i] == S[93])
            R3_f_equ[i] = (R3_f[i] == S[177])  # Dummy variable update

            S[0] = R1_f[i]
            S[93] = R2_f[i]
            S[177] = R3_f[i]
            temp2 = S[:]

            for l in range(state_size):
                hamm_dist_f_equ[i] += (temp1[l] ^ temp2[l])

    if z_act == 1:  # If keystream equation needed
        print("z_act", z_act)
        Equ = Z_f_equ + R1_f_equ + R2_f_equ + R3_f_equ + Z_b_equ + R1_b_equ + R2_b_equ + R3_b_equ
    else:
        print("z_act", z_act)
        Equ = R1_f_equ + R2_f_equ + R3_f_equ + R1_b_equ + R2_b_equ + R3_b_equ

    m.add(Equ)  # Adding equation to the solver

    # Modelling erroneous Hamming distance equations  for both forward and backward directions
    for i in range(N_key_f-1):
        if (hamm_dist_f[i] - tolerance) >= 0:
            # HD_equ >= HD_predicted -tolerance
            m.add(UGE(hamm_dist_f_equ[i], hamm_dist_f[i]-tolerance))
        else:  # Ensure that Hamm_dist_f +- tolerance does not fall outside the modulus
            # i.e. it should lie in the range [0,state_size]
            m.add(UGE(hamm_dist_f_equ[i], 0))

        if (hamm_dist_f[i] + tolerance) <= state_size:
            # HD_equ <= HD_predicted + tolerance
            m.add(ULE(hamm_dist_f_equ[i], hamm_dist_f[i]+tolerance))
        else:
            m.add(ULE(hamm_dist_f_equ[i], state_size))

    for i in range(N_key_b):
        if (hamm_dist_b[i] - tolerance) >= 0:
            # HD_equ >= HD_predicted -tolerance
            m.add(UGE(hamm_dist_b_equ[i], hamm_dist_b[i]-tolerance))
        else:
            m.add(UGE(hamm_dist_b_equ[i], 0))

        if (hamm_dist_b[i] + tolerance) <= state_size:
            # HD_equ <= HD_predicted + tolerance
            m.add(ULE(hamm_dist_b_equ[i], hamm_dist_b[i]+tolerance))
        else:
            m.add(ULE(hamm_dist_b_equ[i], state_size))
    
    if multi_thread == 1:
    	set_param("parallel.enable", True)
    	set_option("parallel.threads.max", n_thread)
    	
    start = time.time()
    temp = m.check()  # Solve SMT instances
    end = time.time()

    if temp == sat:
        print(temp)
        soln = m.model()  # store solution in the soln variable
    else:
        print("###################################unsat###################################################")
        print(temp)
        print(S_org)
        continue
    print("loop", loop)

    print("SMT Time", end - start)
    runtime[loop] = end - start
    out = [0]*state_size
    for i in range(state_size):
        # Extract the values of state variables from the output
        out[i] = soln[S_var_org[i]]
    # print(out)
    # print(S_org)

    if S_org == out:
        print("******************************matched*********************************")
        print("runtime = ", runtime)
        sat_out += 1
    else:
        print("############################not matched##############################################")
        print(S_org)
        print(out)
    sys.stdout.flush()

runtime = np.array(runtime)
print("\n\n Mean =  ")
print(runtime.mean())
print("\n Std = ")
print(runtime.std())
print("\n")


# In[ ]:





# In[ ]:




