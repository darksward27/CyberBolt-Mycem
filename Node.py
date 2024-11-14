import threading
import hashlib
import json
import uuid
from time import time,sleep
import pickle
import socket

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
        self.target_block_time = 60
        self.last_adjustment_time = time()

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

    def withdraw_funds(self, project_name, amount):
        """Withdraw funds from a project's wallet for charity usage with a purpose."""
        if project_name not in self.projects:
            print("Project not found.")
            return None

        project_wallet_id = self.projects[project_name]['wallet_id']
        project_wallet = self.wallets.get(project_wallet_id)

        if project_wallet['balance'] < amount:
            print("Insufficient funds in project wallet.")
            return None

        purpose = input("Enter the purpose of withdrawal: ")

        project_wallet['balance'] -= amount

        withdrawal_log_entry = {
            'type': 'withdrawal',
            'amount': amount,
            'project': project_name,
            'purpose': purpose,
            'timestamp': time()
        }
        self.projects[project_name]['donation_log'].append(withdrawal_log_entry)
        self.current_transactions.append(withdrawal_log_entry)
        print(f"Withdrew {amount} from project '{project_name}' wallet for purpose: {purpose}.")

    def track_funds(self, project_name):
        if project_name not in self.projects:
            print("Project not found.")
            return

        project_data = self.projects[project_name]
        print(f"\nFunds Tracking for Project: {project_name}")
        print(f"Total Donations: {project_data['total_donations']}")
        print("Donation & Withdrawal Log:")
        for entry in project_data['donation_log']:
            print(entry)

    def mine_block_periodically(self):
        while True:
            sleep(60)
            if self.current_transactions:
                last_proof = self.last_block['proof']
                proof = self.proof_of_work(last_proof)
                previous_hash = self.hash(self.last_block)
                self.new_block(proof, previous_hash)
                self.adjust_difficulty()
            else:
                print("No transactions to mine.")

    def execute_contract(self, contract_name, function_name, params):
        contract = self.contracts.get(contract_name)
        if not contract:
            print("Contract not found.")
            return None

        contract_code = contract['code']
        contract_state = contract['state']

        local_scope = {'state': contract_state, 'params': params}
        exec(contract_code, {}, local_scope)

        func = local_scope.get(function_name)
        if not func:
            print(f"Function '{function_name}' not found in contract '{contract_name}'.")
            return None

        return func(contract_state, params)


    def deploy_contract(self, contract_name, contract_code):
        """Deploy a smart contract to the blockchain."""
        self.contracts[contract_name] = {'code': contract_code, 'state': {'donations': [], 'funds': {}}}
        print(f"Contract '{contract_name}' deployed.")


    def show_deployed_contracts(self):
        """Display all deployed contracts on the blockchain."""
        if not self.contracts:
            print("No contracts deployed.")
        else:
            print("\nDeployed Contracts:")
            for contract_name, contract_data in self.contracts.items():
                print(f"Contract Name: {contract_name}")
                print("Contract Code:")
                print(contract_data['code'])
                print("----------")

    def get_donation_contract_code(self):
        """Returns the code for the Donation Contract."""
        return """
        def receive_donation(state, params):
            donor = params.get('donor')
            amount = params.get('amount')
            project = params.get('project')
            state['donations'].append({'donor': donor, 'amount': amount, 'project': project})
            return state['donations']

        def get_donations(state, params):
            return state.get('donations', [])
        """

    def get_allocation_contract_code(self):
        """Returns the code for the Allocation Contract."""
        return """
        def allocate_funds(state, params):
            project = params.get('project')
            amount = params.get('amount')
            if project in state['funds']:
                state['funds'][project] += amount
            else:
                state['funds'][project] = amount
            return state['funds'][project]

        def get_funds(state, params):
            project = params.get('project')
            return state['funds'].get(project, 0)
        """



    def register_node(self, address):
        """Add a new node to the list of nodes."""
        self.nodes.add(address)
        print(f"Node {address} added to the network.")

    def resolve_conflicts(self):
        new_chain = None
        max_length = len(self.chain)

        for node in self.nodes:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(node)
                    s.sendall(pickle.dumps({"action": "chain"}))
                    data = pickle.loads(s.recv(4096))

                    length = data['length']
                    chain = data['chain']

                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain

            except Exception as e:
                print(f"Error connecting to node {node}: {e}")

        if new_chain:
            self.chain = new_chain
            print("Our chain was replaced with a longer valid chain.")
            return True

        print("Our chain is authoritative.")
        return False

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False

            if not self.valid_proof(last_block['proof'], block['proof'], self.difficulty):
                return False

            last_block = block
            current_index += 1

        return True
