import threading
import hashlib
import json
import uuid
from time import sleep,time
import pickle
import socket
import asyncio
from aiohttp import web, ClientSession,ClientTimeout, ClientConnectorError
from jsonrpcserver import Result, Success,async_dispatch as dispatch, method,Error
import ecdsa
import sha3
from hashlib import sha256
import netifaces

peers = {}  # Format: {peer_ip: {'last_sync': timestamp}}
blockchain = None 

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



    def valid_chain(self, chain):
        """Determine if a given blockchain is valid."""
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

    def resolve_conflicts(self):
        """Resolve conflicts by synchronizing with peers that have valid, longer chains."""
        new_state = None
        max_length = len(self.chain)

        for peer in peers:
            try:
                peer_state = asyncio.run(fetch_chain_from_peer(peer))
                if peer_state and len(peer_state.get('chain', [])) > max_length:
                    if self.valid_chain(peer_state['chain']):
                        max_length = len(peer_state['chain'])
                        new_state = peer_state

            except Exception as e:
                print(f"Error retrieving state from peer {peer}: {e}")

    def get_full_state(self):
        """Get the complete state of the blockchain including all data structures."""
        return {
            'chain': self.chain,
            'current_transactions': self.current_transactions,
            'contracts': self.contracts,
            'nodes': list(self.nodes),
            'donation_tokens': self.donation_tokens,
            'projects': self.projects,
            'wallets': self.wallets,
            'token_counter': self.token_counter,
            'difficulty': self.difficulty
        }

    def update_state_from_peer(self, peer_state):
        """Update the blockchain state with data from a peer."""
        if not peer_state:
            return False
        
        # Verify the chain is valid before updating
        if self.valid_chain(peer_state.get('chain', [])):
            if len(peer_state.get('chain', [])) > len(self.chain):
                self.chain = peer_state['chain']
                self.current_transactions = peer_state.get('current_transactions', [])
                self.contracts = peer_state.get('contracts', {})
                self.nodes = set(peer_state.get('nodes', []))
                self.donation_tokens = peer_state.get('donation_tokens', {})
                self.projects = peer_state.get('projects', {})
                self.wallets = peer_state.get('wallets', {})
                self.token_counter = peer_state.get('token_counter', 0)
                self.difficulty = peer_state.get('difficulty', 4)
                return True
        return False


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


@method
async def hello(sender):
    """JSON-RPC method to handle peer registration and initial state sync."""
    try:
        if sender not in peers and sender != local_ip:
            peers[sender] = {'last_sync': 0}
            print(f"New peer added: {sender}")
            
            # Immediately request state from the new peer
            state = await fetch_chain_from_peer(sender)
            if state:
                blockchain.update_state_from_peer(state)
                print(f"Initial state sync completed with peer {sender}")
            
            return Success({"message": f"Hello, {sender}! Added you as a peer.", 
                          "current_state": blockchain.get_full_state()})
    except Exception as e:
        print(f"Error in hello method: {e}")
        return Error(code=-32603, message=str(e))


@method
async def get_chain():
    """JSON-RPC method to provide the complete blockchain state."""
    try:
        full_state = blockchain.get_full_state()
        return Success(full_state)
    except Exception as e:
        print(f"Error getting chain state: {e}")
        return Error(code=-32603, message=str(e))


@method
async def sync_state(state_data: dict) -> Result:
    """JSON-RPC method to receive and process state updates from peers."""
    try:
        if blockchain.update_state_from_peer(state_data):
            # Broadcast to other peers if state was updated
            await broadcast_state_to_peers(state_data)
            return Success("State synchronized and broadcast to peers")
        return Success("Current state is up to date")
    except Exception as e:
        print(f"Error syncing state: {e}")
        return Error(code=-32603, message=str(e))


# JSON-RPC handler for handling incoming requests
async def json_rpc_handler(request):
    # Use async dispatch and do not await the text call twice
    request_text = await request.text()
    response = await dispatch(request_text)
    return web.Response(text=str(response), content_type="application/json")

def remove_inactive_peer(peer_ip):
    """Remove inactive peers from the peers list."""
    if peer_ip in peers:
        del peers[peer_ip]
        print(f"Removed inactive peer: {peer_ip}")


async def fetch_chain_from_peer(peer_ip):
    """Fetch complete blockchain state from a peer with improved error handling."""
    url = f"http://{peer_ip}:5000/jsonrpc"
    payload = {
        "jsonrpc": "2.0",
        "method": "get_chain",
        "params": {},
        "id": str(uuid.uuid4())
    }
    try:
        timeout = ClientTimeout(total=30)  # Increased timeout for larger state transfers
        async with ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    if 'result' in response:
                        print(f"Successfully fetched state from peer {peer_ip}")
                        return response['result']
                print(f"Invalid response from peer {peer_ip}: {resp.status}")
    except asyncio.TimeoutError:
        print(f"Timeout fetching state from peer {peer_ip}")
        remove_inactive_peer(peer_ip)
    except Exception as e:
        print(f"Error fetching state from peer {peer_ip}: {e}")
        remove_inactive_peer(peer_ip)
    return None

async def send_state_to_peer(peer, state_data):
    """Send state to a single peer with error handling."""
    url = f"http://{peer}:5000/jsonrpc"
    payload = {
        "jsonrpc": "2.0",
        "method": "sync_state",
        "params": state_data,
        "id": str(uuid.uuid4())
    }
    try:
        timeout = ClientTimeout(total=30)
        async with ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    peers[peer]['last_sync'] = time()
                    print(f"Successfully broadcast state to peer {peer}")
                else:
                    print(f"Failed to broadcast state to peer {peer}: {resp.status}")
    except Exception as e:
        print(f"Error broadcasting state to peer {peer}: {e}")
        remove_inactive_peer(peer)

async def broadcast_state_to_peers(state_data):
    """Broadcast state updates to all known peers with improved error handling."""
    broadcast_tasks = []
    for peer in list(peers.keys()):  # Create a copy of keys to avoid runtime modification issues
        if peer != local_ip:  # Don't broadcast to self
            task = asyncio.create_task(send_state_to_peer(peer, state_data))
            broadcast_tasks.append(task)
    
    if broadcast_tasks:
        await asyncio.gather(*broadcast_tasks, return_exceptions=True)


# Asynchronous function to initialize the server
async def init_app():
    app = web.Application()
    app.router.add_post("/jsonrpc", json_rpc_handler)
    return app

# Start the server in a separate thread
def run_server(port):
    async def start_server():
        app = await init_app()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"Server is running on http://0.0.0.0:{port}")
        while True:
            await asyncio.sleep(3600)  # Keep the server running

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_server())

def discover_peers(ip, port):
    """Broadcast discovery messages to find peers."""
    broadcast_address = ('<broadcast>', port)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            s.bind((ip, 0))
        except Exception as e:
            print(f"Error binding to address {ip}: {e}")
            return
        while True:
            try:
                s.sendto(b"hello", broadcast_address)
                sleep(5)
            except Exception as e:
                print(f"Error during peer discovery: {e}")
                sleep(5)  # Wait before retrying
                continue

# Function to listen for other peers broadcasting on the network
def listen_for_peers(ip, port):
    """Listen for peer discovery messages."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((ip, port))
        while True:
            try:
                data, addr = s.recvfrom(1024)
                if data == b"hello":
                    peer_ip = addr[0]
                    if peer_ip not in peers and peer_ip != ip:  # Avoid self-connection
                        peers[peer_ip] = {'last_sync': 0}  # Add to peers dictionary with timestamp
                        print(f"Discovered new peer: {peer_ip}")
                        # Attempt to greet the new peer
                        asyncio.run(greet_peer(peer_ip, port))
            except Exception as e:
                print(f"Error in peer listening: {e}")
                sleep(1)

async def greet_peer(peer_ip, port):
    """Send a hello message to a newly discovered peer."""
    url = f"http://{peer_ip}:{port}/jsonrpc"
    payload = {
        "jsonrpc": "2.0",
        "method": "hello",
        "params": {"sender": local_ip},
        "id": str(uuid.uuid4())
    }
    try:
        timeout = ClientTimeout(total=5)  # 5 seconds timeout
        async with ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    print(f"Successfully connected to peer {peer_ip}")
                    response = await resp.json()
                    if 'result' in response and isinstance(response['result'], dict):
                        state_data = response['result'].get('current_state')
                        if state_data:
                            blockchain.update_state_from_peer(state_data)
                            print(f"Received and updated initial state from peer {peer_ip}")
                else:
                    print(f"Failed to connect to peer {peer_ip} with status {resp.status}")
    except TimeoutError:
        print(f"Timeout while connecting to peer {peer_ip}")
        if peer_ip in peers:
            del peers[peer_ip]
    except ClientConnectorError:
        print(f"Connection failed to peer {peer_ip}")
        if peer_ip in peers:
            del peers[peer_ip]
    except Exception as e:
        print(f"Error connecting to peer {peer_ip}: {e}")
        if peer_ip in peers:
            del peers[peer_ip]


def select_network_interface():
    interfaces = netifaces.interfaces()
    print("Available network interfaces:")
    interface_ips = []

    for i, iface in enumerate(interfaces):
        addresses = netifaces.ifaddresses(iface)
        ip = addresses.get(netifaces.AF_INET, [{'addr': None}])[0]['addr']
        if ip:
            print(f"{i}. {iface} ({ip})")
            interface_ips.append(ip)

    selection = int(input("Select the interface by number: "))
    return interface_ips[selection]



# Background task to periodically sync the blockchain with peers
def auto_sync_blockchain():
    """Periodically synchronize the blockchain state with peers."""
    while True:
        try:
            if peers:
                print("\nInitiating blockchain state sync...")
                # Create event loop for async operations
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Sync with all peers
                for peer in list(peers.keys()):
                    try:
                        peer_state = loop.run_until_complete(fetch_chain_from_peer(peer))
                        if peer_state:
                            if blockchain.update_state_from_peer(peer_state):
                                print(f"Successfully synchronized state with peer {peer}")
                                # Broadcast our updated state to other peers
                                loop.run_until_complete(broadcast_state_to_peers(peer_state))
                    except Exception as e:
                        print(f"Error during sync with peer {peer}: {e}")
                        remove_inactive_peer(peer)
                
                loop.close()
            
            sleep(10)  # Sync every 10 seconds
        except Exception as e:
            print(f"Error in auto sync: {e}")
            sleep(5)

# Main function to start the P2P node and blockchain
def main():
    global blockchain, local_ip, peers
    port = 5000
    local_ip = select_network_interface()
    peers = {}  # Initialize empty peers dictionary

    blockchain = Blockchain()

    # Start all the necessary threads
    server_thread = threading.Thread(target=run_server, args=(port,))
    discovery_thread = threading.Thread(target=discover_peers, args=(local_ip, port))
    listener_thread = threading.Thread(target=listen_for_peers, args=(local_ip, port))
    sync_thread = threading.Thread(target=auto_sync_blockchain)

    server_thread.start()
    discovery_thread.start()
    listener_thread.start()
    sync_thread.start()
    mining_thread = threading.Thread(target=blockchain.mine_block_periodically, daemon=True)
    mining_thread.start()

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

        main()
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