from block import *
import datetime
import rsa

# An arbitrarily chosen genesis time of the blockchain
def genesis_time() -> float:
    return datetime.datetime(2022, 5, 9).timestamp()

# An arbitrarily chosen public key for blocks with no signer
genesisKey = rsa.PublicKey(5, 3)

# Gets the current time
def curr_time() -> float:
    return datetime.datetime.now().timestamp()

# Implementing the blockchain class
class BlockChain:

    def __init__(self) -> None:

        # Initialize the blockchain with a genesis block
        genesisBlock = Block(genesisKey, '', '', b'', b'', b'', genesis_time(), blockType = 'Genesis')
        genesisBlock.mineBlock()
        self.chain : list = [genesisBlock]
    
    # Validates, mines and adds a block to the blockchain
    def add(self, block : Block) -> bool:
        if (self.getLastDigest() == block.previousDigest) and block.isMined():
            self.chain.append(block)
            return True
        return False
    
    # Gets the last digest in the blockchain
    def getLastDigest(self) -> bytes:
        previousDigest = self.chain[-1].getDigest()
        return previousDigest

    # Prints the blockchain
    def print(self) -> None:
        for each in self.chain:
            print('-----------------------------------------')
            each.print()