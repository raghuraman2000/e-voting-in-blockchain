from cryptography.hazmat.primitives.hashes import Hash, SHA384
import base64
import rsa
import json

# Helper function to convert int to bytes
def int_to_bytes(x : int) -> bytes:
    return x.to_bytes((x.bit_length() + 7) >> 3, 'big')

# Helper function to convert bytes to base-64 string
def bytes_to_b64str(x : bytes) -> str:
    return base64.b64encode(x).decode('utf-8')

# Class implementing a block in the blockchain
class Block:
    # Parameters for block mining
    prefix_len : int = 1
    prefix_canon : bytes = b'0' * prefix_len

    # Constructor to initialize a block object
    def __init__(self, pubKey : rsa.PublicKey, 
                fromId : str, toId : str, 
                data : bytes, 
                signature : bytes, 
                previousDigest : bytes, 
                timeStamp : float, 
                nonce : int = 0, 
                blockType : str = 'Normal') -> None:

        # Initializing block parameters
        self.blockType : str = blockType
        self.pubKey : rsa.PublicKey = pubKey
        self.fromId :str = fromId
        self.toId :str = toId
        self.data : bytes = data
        self.signature : bytes = signature
        self.previousDigest : bytes = previousDigest
        self.timeStamp : float = timeStamp
        self.nonce : int = nonce
    
    # Function to get the hash of a block data
    def getDigest(self) -> bytes:

        # Converting entire block data into bytes
        completeData : bytes = self.data + self.pubKey.save_pkcs1()
        completeData += (self.fromId + self.toId + self.blockType + str(self.timeStamp)).encode('utf-8')
        completeData += self.signature + self.previousDigest
        completeData += int_to_bytes(self.nonce)

        # Deriving block hash digest
        digest : Hash = Hash(SHA384())
        digest.update(completeData)
        finalDigest = digest.finalize()

        return finalDigest

    # Function to check if the block is mined
    def isMined(self) -> None:
        return (self.getDigest()[ : self.prefix_len] == self.prefix_canon)

    # Mine the block
    def mineBlock(self) -> None:
        self.nonce = 0
        while True:
            if self.isMined():
                break
            self.nonce += 1
    
    # Verify if the signature is proper
    def verifySig(self) -> bool:
        return (rsa.verify(self.data, self.signature, self.pubKey) == 'SHA-384')
    
    # Get dict from the block
    def getDict(self) -> dict:
        blockDict = {
            'pubKeyStr' : bytes_to_b64str(self.pubKey.save_pkcs1()),
            'fromId' : self.fromId,
            'toId' : self.toId,
            'data' : bytes_to_b64str(self.data),
            'signature' : bytes_to_b64str(self.signature),
            'previousDigest' : bytes_to_b64str(self.previousDigest),
            'timeStamp' : str(self.timeStamp),
            'nonce' : str(self.nonce),
            'blockType' : self.blockType
        }
        return blockDict

    # Prints Block
    def print(self) -> None:
        print(json.dumps(self.getDict(), indent = 4))
        print('hash : ', bytes_to_b64str(self.getDigest()))

# Helper function to contruct block object from a dictionary
def block_from_dict(blockDict : dict) -> Block:
    pubKey = rsa.PublicKey.load_pkcs1(base64.b64decode(blockDict['pubKeyStr']))
    data = base64.b64decode(blockDict['data'])
    signature = base64.b64decode(blockDict['signature'])
    previousDigest = base64.b64decode(blockDict['previousDigest'])
    timeStamp = float(blockDict['timeStamp'])
    nonce = int(blockDict['nonce'])
    return Block(pubKey, blockDict['fromId'], blockDict['toId'], data, signature, previousDigest, timeStamp, nonce, blockDict['blockType'])