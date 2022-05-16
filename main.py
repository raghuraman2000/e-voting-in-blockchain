from voter import *
import argparse

# Parsing the command line arugments
def process_args():
    parser = argparse.ArgumentParser(description = 'Peer')
    parser.add_argument('-i', type = int, metavar = 'ID', help = 'The ID of the client')
    args = parser.parse_args()
    return args

args = process_args()
voter = Voter(args.i)
voterInterface = VoterInterface()
voterInterface.init(voter)
voterInterface.cmdloop()