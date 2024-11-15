import ecdsa
import sha3
from hashlib import sha256

def generate_private_key(phrase):
    return sha256(phrase.encode()).hexdigest()

def create_wallet(phrase):
    private_key_hex = generate_private_key(phrase)
    private_key = bytes.fromhex(private_key_hex)
    key = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    public_key = key.get_verifying_key().to_string()
    public_key_hex = public_key.hex()
    keccak = sha3.keccak_256()
    keccak.update(bytes.fromhex(public_key_hex))
    public_address = f"0x{keccak.hexdigest()[-40:]}"
    return {
        "privateKey": private_key_hex,
        "publicKey": public_key_hex,
        "publicAddress": public_address
    }

# Example usage
phrase = ""
wallet = create_wallet(phrase)
print("Private Key:", wallet["privateKey"])
print("Public Key:", wallet["publicKey"])
print("Public Address:", wallet["publicAddress"])
