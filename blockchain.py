import hashlib
import json
from time import time
from urllib.parse import urlparse

import requests


class Blockchain(object):

    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Creates the genesis block
        self.new_block(previous_hash=1, proof=1)

        self.nodes = set()

    def new_block(self, proof, previous_hash=None, seconds_to_proof=None):
        """
        Create a new block in the Blockchain

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (optional) <str> Hash of previous block
        :param seconds_to_proof: (optional) <flt> Time took in seconds to proof
        :return: <dict> New block
        """

        block = {
            'index': len(self.chain),
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'seconds_to_proof': seconds_to_proof
        }

        # Reset current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: <str> Address of sender
        :param recipient: <str> Address of recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """

        tx_index = len(self.current_transactions)

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'timestamp': time(),
            'tx_index': tx_index
        })

        return self.last_block['index'] + 1

    def proof_of_work(self, last_block_hash, last_proof):
        """

        Simple Proof of Work Algorithm

        :param last_block_hash: <int>
        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while True:
            proof_digest = hashlib.sha256(str(proof).encode()).hexdigest()

            if self.valid_proof(last_block_hash, last_proof, proof_digest):
                break
            else:
                proof += 1

        return proof_digest

    @staticmethod
    def valid_proof(last_block_hash, last_proof, proof):
        """
        Validates Proof: Does the Proof contain 4 leading zeros?

        :param last_block_hash: <int> Previous block hash
        :param last_proof: <int> Previous Proof
        :param proof: <int> Proof candidate
        :return: <bool> True if correct, False if not
        """

        # Set the difficulty
        difficulty = 4

        guess = f'{last_block_hash}{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:difficulty] == ('0' * difficulty)

    @staticmethod
    def hash(block):
        """
        Creates a SHA256 hash of a Block

        :param block: <dict> Block
        :return: <str> Hash digest
        """

        # Make sure to order dictionary otherwise we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: <str> Address of node
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: <list>  A blockchain
        :return: <bool> True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1
        chain_length = len(chain)

        while current_index < chain_length:
            current_block = chain[current_index]

            # Check that the hash of the block is correct
            if current_block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the proof of work is correct
            if not self.valid_proof(last_block['proof'], current_block['proof']):
                return False

            last_block = current_block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: <bool> True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we've discovered a new , valid longer chain than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False
