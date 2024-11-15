import asyncio
import threading
import time
import socket
import json
import netifaces
from aiohttp import web
from jsonrpcserver import method, dispatch

# Global list to store peers
peers = set()

# JSON-RPC method to add a peer
@method
async def hello(sender):
    if sender not in peers:
        peers.add(sender)
        print(f"New peer added: {sender}")
    return f"Hello, {sender}! Added you as a peer."

# JSON-RPC handler for handling incoming requests
async def json_rpc_handler(request):
    response = await dispatch(await request.text())
    return web.Response(text=response, content_type="application/json")

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

# Display available network interfaces
# Function to display and select a network interface
def select_network_interface():
    interfaces = netifaces.interfaces()
    available_interfaces = []
    print("Available network interfaces:")

    # List interfaces with IPv4 addresses only
    for i, iface in enumerate(interfaces):
        # Check if the interface has an IPv4 address
        if netifaces.AF_INET in netifaces.ifaddresses(iface):
            ip_info = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]
            ip_address = ip_info['addr']
            print(f"{i}. {iface} (IP: {ip_address})")
            available_interfaces.append((iface, ip_address))

    # Get user selection
    selection = int(input("Select the interface by number: "))
    selected_interface, ip_address = available_interfaces[selection]
    print(f"Selected interface {selected_interface} with IP {ip_address}")
    return ip_address

# Function to discover other nodes by broadcasting on the network
def discover_peers(ip, port):
    broadcast_address = ('<broadcast>', port)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind((ip, 0))  # Bind to the selected interface
        while True:
            try:
                s.sendto(b"hello", broadcast_address)
                time.sleep(5)  # Broadcast every 5 seconds
            except Exception as e:
                print(f"Error during peer discovery: {e}")
                break

# Function to listen for other peers broadcasting on the network
def listen_for_peers(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((ip, port))
        while True:
            data, addr = s.recvfrom(1024)
            if data == b"hello":
                peer_ip = addr[0]
                if peer_ip not in peers:
                    peers.add(peer_ip)
                    print(f"Discovered new peer: {peer_ip}")
                    # Attempt to greet the new peer
                    asyncio.run(greet_peer(peer_ip, port))

# Function to send a "hello" message to a peer using JSON-RPC
async def greet_peer(peer_ip, port):
    url = f"http://{peer_ip}:{port}/jsonrpc"
    payload = {
        "jsonrpc": "2.0",
        "method": "hello",
        "params": {"sender": "localhost"},
        "id": 1
    }
    try:
        async with web.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    print(f"Successfully connected to peer {peer_ip}")
                else:
                    print(f"Failed to connect to peer {peer_ip} with status {resp.status}")
    except Exception as e:
        print(f"Error connecting to peer {peer_ip}: {e}")

# Display peers (for testing/debugging)
def display_peers():
    while True:
        print("Current peers:", peers)
        time.sleep(10)

# Main function to start the P2P node
def main():
    port = 5000  # Each node will listen on this port
    ip_address = select_network_interface()  # User selects the network interface

    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server, args=(port,))
    server_thread.start()

    # Start broadcasting discovery messages
    discovery_thread = threading.Thread(target=discover_peers, args=(ip_address, port))
    discovery_thread.start()

    # Start listening for other nodes
    listener_thread = threading.Thread(target=listen_for_peers, args=(ip_address, port))
    listener_thread.start()

    # Start a display thread to show current peers
    display_thread = threading.Thread(target=display_peers)
    display_thread.start()

# Run the main function to start the P2P node
if __name__ == "__main__":
    main()
