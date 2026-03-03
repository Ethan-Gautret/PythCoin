# Mini Blockchain — Python

Implémentation didactique d'une blockchain fonctionnelle avec réseau P2P,
wallets, signatures cryptographiques et smart contracts.

## Installation
```bash
git clone <repo>
cd blockchain_project
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Lancer un réseau multi-nœuds (3 nœuds)

Ouvrir 3 terminaux :
```bash
# Terminal 1 — Nœud principal
python node.py --port 5000 --name Node1 --difficulty 3

# Terminal 2 — Nœud 2 (connecté au nœud 1)
python node.py --port 5001 --name Node2 --difficulty 3 --peer 127.0.0.1:5000

# Terminal 3 — Nœud 3 (connecté au nœud 1)
python node.py --port 5002 --name Node3 --difficulty 3 --peer 127.0.0.1:5000
```

## Démonstration complète

### 1. Créer un wallet et envoyer une transaction
```python
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
```

### 2. Miner un bloc
```bash
curl -X POST http://127.0.0.1:5000/mine
```

### 3. Vérifier la propagation
```bash
curl http://127.0.0.1:5001/chain   # Le bloc doit apparaître ici
curl http://127.0.0.1:5002/chain   # Et ici
```

### 4. Déployer et exécuter un smart contract
```bash
# Déployer un compteur
curl -X POST http://127.0.0.1:5000/contracts/deploy \
  -H "Content-Type: application/json" \
  -d '{"type":"counter","id":"counter-1","owner":"0xABC"}'

# Exécuter via une transaction
curl -X POST http://127.0.0.1:5000/transactions/new \
  -H "Content-Type: application/json" \
  -d '{"sender":"0xABC","receiver":"counter-1","amount":0,"nonce":0,"data":{"action":"increment"},"signature":"","id":"tx-1"}'

# Vérifier l'état
curl http://127.0.0.1:5000/contracts/counter-1
```

## Lancer les tests
```bash
pytest tests/ -v
```

## Architecture
```
src/
  crypto/       → CryptoUtils (hash, sign, verify, dérivation d'adresse)
  core/         → Transaction, Block, Blockchain, WorldState
  p2p/          → Peer, P2PNetwork (broadcast, anti-boucle, synchronisation)
  contracts/    → SmartContract, ContractEngine, CounterContract, EscrowContract
  wallet/       → Wallet (génération clés, signature transactions)
node.py         → Serveur Flask — API REST du nœud
tests/          → Tests pytest (crypto, transactions, blockchain, P2P, contracts)
```

## Modèle de données

- **Transaction** : sender, receiver, amount, nonce, signature, data
- **Block** : index, timestamp, transactions, previous_hash, nonce, merkle_root, hash
- **Blockchain** : chain (liste de blocs liés), difficulty (PoW)
- **WorldState** : balances (dict adresse→solde), contracts (dict id→état)

## Sécurité

- Signatures EC (SECP256K1) — même courbe que Bitcoin
- Prévention du rejeu par nonce (incrémenté par adresse)
- Preuve de travail (PoW) configurable par difficulté
- Validation de chaîne complète (hash + Merkle root + PoW)
- Anti-boucle P2P par identifiant de message unique