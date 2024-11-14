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
