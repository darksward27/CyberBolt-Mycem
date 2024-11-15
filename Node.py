import threading
import hashlib
import json
import uuid
from time import time,sleep
import pickle
import socket
import asyncio
from aiohttp import web
from jsonrpcserver import Result, Success, dispatch, method
import ecdsa
import sha3
from hashlib import sha256


class Node:
    pass

class LeafNode(Node):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def serialize(self):
        return pickle.dumps(self)

    @staticmethod
    def deserialize(data):
        return pickle.loads(data)

class ExtensionNode(Node):
    def __init__(self, key, next_node):
        self.key = key
        self.next_node = next_node

    def serialize(self):
        return pickle.dumps(self)

    @staticmethod
    def deserialize(data):
        return pickle.loads(data)

class BranchNode(Node):
    def __init__(self):
        self.branches = [None] * 16
        self.value = None

    def serialize(self):
        return pickle.dumps(self)

    @staticmethod
    def deserialize(data):
        return pickle.loads(data)

class MerklePatriciaTrie:
    def __init__(self):
        self.root = BranchNode()

    def insert(self, key, value):
        encoded_key = self._encode_key(key)
        self._insert(self.root, encoded_key, value)

    def _insert(self, node, key, value):
        if isinstance(node, BranchNode):
            if not key:
                node.value = value
            else:
                index = key[0]
                if node.branches[index] is None:
                    node.branches[index] = LeafNode(key[1:], value)
                else:
                    self._insert(node.branches[index], key[1:], value)
        elif isinstance(node, LeafNode):
            common_prefix = self._common_prefix(node.key, key)
            if common_prefix == len(node.key):
                node.value = value
            else:
                branch = BranchNode()
                branch.branches[node.key[common_prefix]] = node
                branch.branches[key[common_prefix]] = LeafNode(key[common_prefix + 1:], value)
                node.key = node.key[:common_prefix]
                node.next_node = branch

    def fetch(self, key):
        encoded_key = self._encode_key(key)
        return self._fetch(self.root, encoded_key)

    def _fetch(self, node, key):
        if isinstance(node, BranchNode):
            if not key:
                return node.value
            index = key[0]
            if node.branches[index] is None:
                return None
            return self._fetch(node.branches[index], key[1:])
        elif isinstance(node, LeafNode):
            if node.key == key:
                return node.value
            return None
        return None

    def save_to_file(self, file_path):
        with open(file_path, 'wb') as f:
            f.write(self.root.serialize())

    def load_from_file(self, file_path):
        with open(file_path, 'rb') as f:
            self.root = BranchNode.deserialize(f.read())

    @staticmethod
    def _encode_key(key):
        return bytes([int(c, 16) for c in key])

    @staticmethod
    def _common_prefix(a, b):
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                return i
        return min(len(a), len(b))

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
        self.deploy_contract('DonationContract', self.get_donation_contract_code())
        self.deploy_contract('AllocationContract', self.get_allocation_contract_code())

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

    def create_wallett(self,owner_name):
        def generate_private_key(phrase):
            return sha256(phrase.encode()).hexdigest()
        private_key_hex = generate_private_key(owner_name)
        private_key = bytes.fromhex(private_key_hex)
        key = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
        public_key = key.get_verifying_key().to_string()
        public_key_hex = public_key.hex()
        keccak = sha3.keccak_256()
        keccak.update(bytes.fromhex(public_key_hex))
        public_address = f"0x{keccak.hexdigest()[-40:]}"
        self.wallets[public_address] = {'owner': owner_name, 'balance': 1000, 'private_key': private_key_hex}
        print(f"Wallet created for {owner_name} with ID: {public_address}")
        return public_address,private_key_hex

    def add_project(self, project_name,wallet_id):
        if project_name in self.projects:
            return "404"
        else:
            self.projects[project_name] = {
                'total_donations': 0,
                'wallet_id': wallet_id,
                'donation_log': []
            }
            return '200'

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
            return "404"

        donor_wallet = self.wallets.get(wallet_id)
        if not donor_wallet:
            print("Wallet not found.")
            return "404"

        if donor_wallet['balance'] < amount:
            print("Insufficient balance in wallet.")
            return "403"

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


def display_blockchain(blockchain):
    print("\nBlockchain:")
    for block in blockchain.chain:
        print(json.dumps(block, indent=4))

db = MerklePatriciaTrie()



@method
def create_wallet(message: list) -> Result:
    print("Received wallet:", message['publicAddress'])
    print("Received user name:", message['uname'])

    wallet = blockchain.wallets.get(message['publicAddress'])
    if wallet:
        return Success("wallet address already added")
    else:
        blockchain.wallets[str(message['publicAddress'].replace('0x', ''))] = {'owner':message['uname'], 'balance': 1000}
        return Success("wallet address recived successfully")


@method
def create_project(message: list) -> Result:
    print("Received wallet:", message['publicAddress'])
    print("Received name:", message['pname'])
    blockchain.wallets[str(message['publicAddress'].replace('0x', ''))] = {'owner': message['pname'], 'balance': 100}
    result = blockchain.add_project(message['pname'],message['publicAddress'])
    if result == '200':
        return Success("wallet address already added")
    else:
        db.insert(str(message['publicAddress'].replace('0x', '')),"0")
        return Success("wallet address recived successfully")


@method
def check_balance(message: str) -> Result:
    print(message['wall'])
    wallet = blockchain.wallets.get(str(message['wall'].replace('0x', '')))
    if wallet:
        bal = blockchain.wallets.get(str(message['wall'].replace('0x', '')))
        return Success(bal['balance'])
    else:
        return Success("404")


@method
def check_files(message: str) -> Result:
    print(message['wall'])
    project_list = list(blockchain.projects.keys())
    if project_list:
        flist = [{"name": project} for project in project_list]
        return Success(flist)
    else:
        return Success("No files Uploaded")


async def json_rpc_handler(request):
    return web.Response(text=dispatch(await request.text()), content_type="application/json")

server_ready = threading.Event()




async def init_app():
    app = web.Application()
    app.router.add_post("/jsonrpc", json_rpc_handler)
    return app

def run_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = loop.run_until_complete(init_app())
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    loop.run_until_complete(site.start())
    server_ready.set() 
    loop.run_forever()




server_thread = threading.Thread(target=run_server)
server_thread.start()


server_ready.wait()

def show_menu():
    print("\nChoose an option:")
    print("1. Add a New Project")#
    print("2. Create a Wallet")#
    print("3. Check Wallet Balance")#
    print("4. Add a Donation to an Existing Project")
    print("5. Track Funds for a Project")
    print("6. Withdraw Funds from Project Wallet")#
    print("7. Display Blockchain")#
    print("8. Deploy a Smart Contract")#
    print("9. Execute a Smart Contract Function")#
    print("10. Show Deployed Contracts")#
    print("11. Register a New Node")
    print("12. Resolve Conflicts")
    print("13. Exit")#

# Keep the main thread alive
try:
    while True:
        blockchain = Blockchain()
        mining_thread = threading.Thread(target=blockchain.mine_block_periodically, daemon=True)
        mining_thread.start()
        while True:
            show_menu()
            choice = input("Enter your choice: ")

            if choice == "1":
                project_name = input("Enter project name: ")
                wall,p=blockchain.create_wallett(project_name)
                blockchain.add_project(project_name,wall)

            elif choice == "2":
                owner_name = input("Enter wallet owner name: ")
                wallet_id, private_key = blockchain.create_wallett(owner_name)
                print(f"Wallet ID: {wallet_id}")
                print(f"Private Key: {private_key}")

            elif choice == "3":
                wallet_id = input("Enter wallet ID: ")
                balance = blockchain.check_wallet_balance(wallet_id)
                if balance is not None:
                    print(f"Wallet balance: {balance}")

            elif choice == "4":
                if not blockchain.projects:
                    print("No projects available. Add a project first.")
                else:
                    wallet_id = input("Enter your wallet ID: ")
                    amount = float(input("Enter donation amount: "))
                    print("Choose a project:")
                    for idx, project in enumerate(blockchain.projects.keys(), start=1):
                        print(f"{idx}. {project}")
                    project_choice = int(input("Enter project number: ")) - 1
                    project_name = list(blockchain.projects.keys())[project_choice]
                    blockchain.new_donation(wallet_id, amount, project_name)

            elif choice == "5":
                project_name = input("Enter project name to track funds: ")
                blockchain.track_funds(project_name)

            elif choice == "6":
                project_name = input("Enter project name for fund withdrawal: ")
                amount = float(input("Enter amount to withdraw: "))
                blockchain.withdraw_funds(project_name, amount)

            elif choice == "7":
                display_blockchain(blockchain)

            elif choice == "8":
                contract_name = input("Enter contract name: ")
                contract_code = input("Enter contract code:\n")
                blockchain.deploy_contract(contract_name, contract_code)

            elif choice == "9":
                contract_name = input("Enter contract name: ")
                function_name = input("Enter function name to execute: ")
                params = eval(input("Enter parameters as a dictionary (e.g., {'amount': 100}): "))
                result = blockchain.execute_contract(contract_name, function_name, params)
                print(f"Result from contract function '{function_name}':", result)

            elif choice == "10":
                blockchain.show_deployed_contracts()

            elif choice == "11":
                node_ip = input("Enter node IP address: ")
                node_port = int(input("Enter node port number: "))
                blockchain.register_node((node_ip, node_port))
                print(f"Node {node_ip}:{node_port} added.")

            elif choice == "12":
                blockchain.resolve_conflicts()

            elif choice == "13":
                print("Exiting...")
                break

            else:
                print("Invalid choice. Please try again.")

except KeyboardInterrupt:
    print("Shutting down...")