import socket

def scan_for_open_port(port=9024, subnet="192.168.1"):
    open_ports = []

    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)

        result = sock.connect_ex((ip, port))
        if result == 0:
            open_ports.append((ip, port))
        sock.close()

    return open_ports


open_ports = scan_for_open_port()
if open_ports:
    for ip, port in open_ports:
        print(f"Open port {port} found at IP: {ip}")
else:
    print("No open ports found on the subnet.")
