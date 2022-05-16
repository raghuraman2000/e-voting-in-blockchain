# README

## Requirements

The following python libraries are required for the execution of the program, and they can be installed using pip - cryptography, rsa, p2pnetwork. There is a requirements.txt file for one step installation of requirements.

```bash
pip3 install -r requirements.txt
```

## Checks

Before execution, please make sure that the all the python scripts - block.py, blockchain.py, voter.py and main.py are in the same directory. Additionally, make sure that there is a directory named registered_voters that is **EMPTY**.

## Execution

Every voter can be run using their own process instance of the main.py file as follows

```bash
python main.py -i 67
```

A unique ID (between 0 and 1000) must be assigned to every voter instance that is created using the command line argument option '-i' for the proper functioning of the program. Additionally, note that **ALL** the voter processes must be started **BEFORE** running any commands in the voter interface.

## Voter Interface

Once a voter process is started, a command line voter interface pops up with the following permissible commands:

- vote **CandidateId** : Gets permission from blockchain members and prepares a vote for the Candidate with ID **CandidateId**
- ballot : Casts the vote anonymously in the blockchain
- count : Counts and tallys all the votes casted in the blockchain until now
- print : Prints the entire blockchain
