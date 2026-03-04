from src.wallet.wallet import Wallet
from src.crypto.crypto_utils import CryptoUtils
import requests, json

# Créer deux wallets
alice = Wallet(); alice.generate_keys()
bob = Wallet();   bob.generate_keys()

# Demander solde initial (0)
r = requests.get(f"http://127.0.0.1:5000/balance/{alice.address}")
print(r.json())

# Créer une transaction signée
tx = alice.create_transaction(bob.address, 10.0, nonce=0)
payload = tx.to_full_dict()
payload["public_key_pem"] = alice.public_key_pem

r = requests.post("http://127.0.0.1:5000/transactions/new", json=payload)
print(r.json())