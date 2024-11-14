import threading
import hashlib
import json
import uuid
from time import time,sleep

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

        self.difficulty = 4
        self.create_genesis_block()

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

    def proof_of_work(self, last_proof):
        proof = 0
        while not self.valid_proof(last_proof, proof, self.difficulty):
            proof += 1
        return proof

    def adjust_difficulty(self):
        if len(self.chain) < 2:
            return

        current_time = time()
        time_taken = current_time - self.last_adjustment_time
        expected_time = self.target_block_time * len(self.chain)
        if time_taken < expected_time / 2:
            self.difficulty += 1
            print(f"Increasing difficulty to {self.difficulty}")

        elif time_taken > expected_time * 2:
            self.difficulty = max(1, self.difficulty - 1)
            print(f"Decreasing difficulty to {self.difficulty}")

        self.last_adjustment_time = current_time


    @staticmethod
    def valid_proof(last_proof, proof, difficulty):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == "0" * difficulty

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def create_wallet(self, owner_name):
        wallet_id = str(uuid.uuid4())
        private_key = str(uuid.uuid4())
        self.wallets[wallet_id] = {'owner': owner_name, 'balance': 1000, 'private_key': private_key}
        print(f"Wallet created for {owner_name} with ID: {wallet_id}")
        return wallet_id, private_key

    def add_project(self, project_name):
        if project_name in self.projects:
            print("Project already exists.")
        else:
            wallet_id, private_key = self.create_wallet(project_name)
            self.projects[project_name] = {
                'total_donations': 0,
                'wallet_id': wallet_id,
                'donation_log': []
            }
            print(f"Project '{project_name}' added with wallet ID: {wallet_id}")

    def check_wallet_balance(self, wallet_id):
        wallet = self.wallets.get(wallet_id)
        if wallet:
            return wallet['balance']
        else:
            print("Wallet not found.")
            return None

    def new_donation(self, wallet_id, amount, project_name):
        if project_name not in self.projects:
            print("Project not found.")
            return None

        donor_wallet = self.wallets.get(wallet_id)
        if not donor_wallet:
            print("Wallet not found.")
            return None

        if donor_wallet['balance'] < amount:
            print("Insufficient balance in wallet.")
            return None

        donor_wallet['balance'] -= amount

        project_wallet_id = self.projects[project_name]['wallet_id']
        self.wallets[project_wallet_id]['balance'] += amount

        token_id = f"donation_{self.token_counter}_{uuid.uuid4()}"
        self.token_counter += 1
        donation_log_entry = {
            'type': 'donation',
            'donor': donor_wallet['owner'],
            'amount': amount,
            'project': project_name,
            'token_id': token_id,
            'timestamp': time()
        }
        self.projects[project_name]['donation_log'].append(donation_log_entry)
        self.projects[project_name]['total_donations'] += amount
        self.current_transactions.append(donation_log_entry)
        print(f"Donation added with token ID: {token_id} to project '{project_name}' by {donor_wallet['owner']}")
        return token_id