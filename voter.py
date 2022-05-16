from cmd import Cmd
from p2pnetwork.node import Node
import rsa
import os
from time import sleep
from block import *
from blockchain import *

def registeredVoterPath(voterId : str) -> str:
    return ('./registered_voters/' + voterId + '.pem')

# Get the public key of a voter
def get_pub_key(blockId : str) -> rsa.PublicKey:
    with open(registeredVoterPath(blockId), 'rb') as r:
        pubKey = rsa.PublicKey.load_pkcs1(r.read())
        r.close()
    return pubKey

# Get the set of all registered voters
def getRegisteredVoters() -> set:
    registeredVoters = set()
    for each in os.listdir('./registered_voters'):
        registeredVoters.add(int(each[:-4]))
    return registeredVoters

# Verifies the voter
def verifyVoter(nodeId : str) -> bool:
    return os.path.isfile(registeredVoterPath(nodeId))

# Class to represent a candidate
class Candidate:

    candidateTotal = 31
    candidateIdBits = 4

    def __init__(self, candidateId : int):
        if candidateId <= self.candidateTotal:
            self.candidateId = candidateId

    def getVoteHash(self, voteRandom = b'') -> int:

        # Generate the vote string bytes
        voteBytes = self.candidateId.to_bytes(self.candidateIdBits, 'big') + b'\0' * self.candidateIdBits
        if voteRandom == b'':
            voteRandom = os.urandom(self.candidateIdBits)
        voteBytes += voteRandom

        # Get the hash digest of the vote bytes
        voteHash = Hash(SHA384())
        voteHash.update(voteBytes)
        voteHashInt = int.from_bytes(voteHash.finalize(), 'big')

        return voteHashInt, voteRandom

# Class to represent a voter
class Voter:
    keySize = 2048
    portMin = 10000
    hostip = "127.0.0.1"

    def __init__(self, voterId: int):
        self.voterId = voterId

        # Generate key pairs for the voter
        self.pubKey, self.privKey = rsa.newkeys(self.keySize)
        self.pubKeyStr : str = bytes_to_b64str(self.pubKey.save_pkcs1())

        # Connect the voter to the peer-to-peer network
        selfPort = self.portMin + voterId
        self.blocknode = Node(self.hostip, selfPort, voterId, self.node_callback)
        self.blocknode.start()
        for nodeId in getRegisteredVoters():
            if nodeId != voterId:
                self.blocknode.connect_with_node(self.hostip, self.portMin + nodeId)
        
        # Intialize blockchain and helper variables
        self.blockchain = BlockChain()
        self.blind_invs = dict()
        self.signs = dict()
        self.voted = set()
    
    # Register this voter
    def register(self) -> None:
        with open(registeredVoterPath(self.blocknode.id), 'wb') as w:
            w.write(self.pubKey.save_pkcs1())
            w.close()

    # Gets the other required parameters and constructs a new block
    def getNewBlock(self, toId : str, data : bytes, blockType : str) -> Block:
        sign = rsa.sign(data, self.privKey, 'SHA-384')
        previousDigest = self.blockchain.getLastDigest()
        newBlock = Block(self.pubKey, self.blocknode.id, toId, data, sign, previousDigest, curr_time(), blockType = blockType)
        newBlock.mineBlock()
        return newBlock
    
    # Create the vote block
    def getVoteBlock(self, voteHashInt : int, nodeId : str) -> Block:
        
        # Get the publice key of the node and blind the message
        pubKey = get_pub_key(nodeId)
        blind_msg, blind_inv = pubKey.blind(voteHashInt)
        self.blind_invs[nodeId] = blind_inv
        voteDataBytes = int_to_bytes(blind_msg)

        return self.getNewBlock(nodeId, voteDataBytes, 'Vote')
    
    # Create the sign block
    def getSignBlock(self, voteBlock : Block) -> Block:

        # Signs the blinded message
        blind_msg = int.from_bytes(voteBlock.data, 'big')
        blind_sign = rsa.core.encrypt_int(blind_msg, self.privKey.d, self.privKey.n)
        signDataBytes = int_to_bytes(blind_sign)

        return self.getNewBlock(voteBlock.fromId, signDataBytes, 'Sign')
    
    # Add vote sign
    def addVoteSign(self, signBlock : Block) -> None:
        pubKey = get_pub_key(signBlock.fromId)
        blind_inv = self.blind_invs[signBlock.fromId]
        unblinded = pubKey.unblind(int.from_bytes(signBlock.data, 'big'), blind_inv)
        self.signs[signBlock.fromId] = unblinded

    # Broadcast the vote
    def vote(self, voteChoice : int):

        # Get the hash of the vote string
        self.voteChoice = voteChoice
        voteHashInt, self.voteRandom = Candidate(self.voteChoice).getVoteHash()

        # Sign the vote string of self
        self.signs[self.blocknode.id] = rsa.core.encrypt_int(voteHashInt, self.privKey.d, self.privKey.n)

        # Send the vote string hash to all nodes to get the signature
        for node in self.blocknode.all_nodes:
            voteBlock = self.getVoteBlock(voteHashInt, node.id)
            if self.blockchain.add(voteBlock):
                self.blocknode.send_to_nodes(voteBlock.getDict())
            while str(node.id) not in self.signs.keys():
                sleep(0.1)
            
    
    # Cast the vote
    def castBallot(self):

        # Construct the ballot
        ballotBlockDict = {
            'voteChoice' : self.voteChoice,
            'voteRandom' : int.from_bytes(self.voteRandom, 'big')
        }
        ballotBlockDict.update(self.signs)
        ballotBlockData = json.dumps(ballotBlockDict).encode('utf-8')

        # Construct the ballot block
        previousDigest = self.blockchain.getLastDigest()
        ballotBlock = Block(genesisKey, '', '', ballotBlockData, b'', previousDigest, curr_time(), blockType = 'Ballot')
        ballotBlock.mineBlock()

        # Add ballot block to the blockchain
        if self.blockchain.add(ballotBlock):
            self.blocknode.send_to_nodes(ballotBlock.getDict())
    
    # Counts the valid votes and tallys them
    def count(self) -> None:
        tallyList = [ 0 for _ in range(Candidate.candidateTotal + 1)]
        seenBallot = set()
        registeredVoters = getRegisteredVoters()
        for block in self.blockchain.chain:
            if block.blockType == 'Ballot':
                ballotDict = json.loads(block.data)
                voteRandom = int(ballotDict['voteRandom']).to_bytes(Candidate.candidateIdBits, 'big')
                voteChoice = int(ballotDict['voteChoice'])
                voteHashInt, _ = Candidate(voteChoice).getVoteHash(voteRandom)
                voteValid = True
                for voterId in registeredVoters:
                    if str(voterId) not in ballotDict.keys():
                        voteValid = False
                        break
                    pubKey = get_pub_key(str(voterId))
                    voteDec = rsa.core.decrypt_int(int(ballotDict[str(voterId)]), pubKey.e, pubKey.n)
                    if voteDec != voteHashInt:
                        voteValid = False
                        break
                if voteValid and voteHashInt not in seenBallot:
                    tallyList[voteChoice] += 1
                    seenBallot.add(voteHashInt)
                    
        print('Candidate', 'Votes', sep = '\t')
        for idx, each in enumerate(tallyList):
            if each > 0:
                print(idx, each, sep = '\t\t')

    # Stops the voter node
    def stop(self) -> None:
        os.remove(registeredVoterPath(self.blocknode.id))
        self.blocknode.stop()
    
    # P2P Node callback
    def node_callback(self, event, node, connected_node, data) -> None:
        if event == 'node_message':
            newBlock = block_from_dict(data)

            if newBlock.blockType == 'Vote' and verifyVoter(newBlock.fromId):
                if self.blockchain.add(newBlock) and (newBlock.toId == self.blocknode.id) and (newBlock.fromId not in self.voted):
                    self.voted.add(newBlock.fromId)
                    signBlock = self.getSignBlock(newBlock)
                    self.blockchain.add(signBlock)
                    self.blocknode.send_to_nodes(signBlock.getDict())

            elif newBlock.blockType == 'Sign' and verifyVoter(newBlock.fromId):
                if self.blockchain.add(newBlock) and (newBlock.toId == self.blocknode.id):
                    self.addVoteSign(newBlock)
            
            elif newBlock.blockType == 'Ballot':
                self.blockchain.add(newBlock)

# Custom voter command interface
class VoterInterface(Cmd):
    intro = 'Welcome to the Voter Interface. Type ? or help to list commands\n'
    prompt = '(voter) '

    def init(self, voter: Voter):
        self.voter = voter
        self.voter.register()
    
    # Broadcast the vote
    def do_vote(self, args):
        'Broadcasts the voting block'
        voteChoice = int(args)
        self.voter.vote(voteChoice)
    
    # Cast the vote
    def do_ballot(self, args):
        'Casts the vote using a ballot block'
        self.voter.castBallot()
    
    # Count the votes to get the results
    def do_count(self, args):
        'Counts all the valid votes and tallys the results'
        self.voter.count()
    
    # Print the blockchain
    def do_print(self, args):
        'Prints the blockchain'
        self.voter.blockchain.print()
    
    # Stop the voter interface
    def do_stop(self, args):
        'Exits the prompt'
        self.voter.stop()
        return True