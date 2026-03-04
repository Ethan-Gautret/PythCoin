from src.wallet.wallet import Wallet
import requests

# Créer deux wallets
alice = Wallet(); alice.generate_keys()
bob = Wallet();   bob.generate_keys()

print(f"Alice: {alice.address}")
print(f"Bob:   {bob.address}")

# Étape 1 — Miner un bloc vide pour qu'Alice reçoive la récompense
r = requests.post("http://127.0.0.1:5000/mine", json={"miner_address": alice.address})
print("Mine 1:", r.status_code, r.text[:80])

# Étape 2 — Vérifier le solde d'Alice (doit être 10.0)
r = requests.get(f"http://127.0.0.1:5000/balance/{alice.address}")
print("Solde Alice:", r.json())

# Étape 3 — Alice envoie 5 coins à Bob
tx = alice.create_transaction(bob.address, 5.0, nonce=0)
payload = tx.to_full_dict()
payload["public_key_pem"] = alice.public_key_pem
r = requests.post("http://127.0.0.1:5000/transactions/new", json=payload)
print("Transaction:", r.json())

# Étape 4 — Miner pour confirmer la transaction
r = requests.post("http://127.0.0.1:5000/mine", json={"miner_address": alice.address})
print("Mine 2 status:", r.status_code)
if r.text:
    print("Mine 2:", r.json())

# Étape 5 — Vérifier les soldes finaux
print("Solde Alice:", requests.get(f"http://127.0.0.1:5000/balance/{alice.address}").json())
print("Solde Bob:",   requests.get(f"http://127.0.0.1:5000/balance/{bob.address}").json())