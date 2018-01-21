from uuid import uuid4

from flask import Flask, jsonify, request

from blockchain import Blockchain


# Instantiate a node
app = Flask(__name__)

# Global identifier for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['GET'])
def mine():
    # Run proof of work algorithm to get the next proof
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We receive as reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1
    )

    # Forge new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': 'New Block Forged',
        'index': block['index'],
        'transaction': block['transactions'],
        'proof': block['proof'],
        'block': block['previous_hash']
    }
    return jsonify(response), 200


@app.route('/transaction/new', methods=['POST'])
def new_transaction():
    values = request.json()

    # Check the required fields are in the request data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    message = {'message': f'Transaction will be added to Block index {index}'}
    return jsonify(message), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
