import os
import json

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