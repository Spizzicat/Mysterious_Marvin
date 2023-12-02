import os
import json
import matplotlib.pylab as plt

DIR = os.getcwd()

def read_bank():

    with open(f'{DIR}/data/bank.json','r') as file:
        newbank = json.loads(file.read())

    newbank.setdefault('companies',{}) 
    newbank.setdefault('accounts',{}) 
    return newbank

def write_bank(bank):

    with open(f'{DIR}/data/bank.json','w') as file:
        json.dump(bank, file, indent=4)
    file.close()

# def csc(x):
#     if plt.sin(x) != 0:
#         return 1/plt.sin(x)
#     else:
#         return None

# def sec(x):
#     if plt.cos(x) != 0:
#         return 1/plt.cos(x)
#     else:
#         return None

# def cot(x):
#     if plt.tan(x) != 0:
#         return 1/plt.tan(x)
#     else:
#         return None