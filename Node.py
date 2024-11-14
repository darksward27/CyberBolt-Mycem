import threading
import hashlib
import time

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.contracts = {}
        self.nodes = set()
        self.donation_tokens = {}
        self.projects = {}
        self.wallets = {}
        self.token_counter = 0

    def create_genesis_block(self):
            genesis_block = {
                'index': 1,
                'timestamp': time(),
                'transactions': [],
                'proof': 100,
                'previous_hash': '1',
            }
            self.chain.append(genesis_block)
            print("Genesis block created")

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
        print(f"New block mined and added to the blockchain with index: {block['index']}")
        return block

    def new_transaction(self, sender, recipient, amount, contract_name=None, function_name=None, params=None):
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'contract': contract_name,
            'function': function_name,
            'params': params,
        }
        self.current_transactions.append(transaction)
        return self.last_block['index'] + 1

