# PythCoin — Mini Blockchain Python

Implémentation didactique d'une blockchain fonctionnelle avec réseau P2P,
wallets, signatures cryptographiques et smart contracts.

Projet réalisé dans le cadre du cours Blockchain — Doranco / Nexa Digital School.

---

## Installation
```bash
git clone <repo>
cd PythCoin
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

---

## Lancer un réseau multi-nœuds (3 nœuds)

Ouvrir 3 terminaux séparés :
```bash
# Terminal 1 — Nœud principal
python node.py --port 5000 --name Node1 --difficulty 3

# Terminal 2
python node.py --port 5001 --name Node2 --difficulty 3

# Terminal 3
python node.py --port 5002 --name Node3 --difficulty 3
```

---

## Connecter les nœuds entre eux

Dans un 4ème terminal (PowerShell) :
```powershell
# Node1 connaît Node2 et Node3
Invoke-WebRequest -Uri http://127.0.0.1:5000/peers/add -Method POST -ContentType "application/json" -Body '{"address":"127.0.0.1","port":5001}' -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:5000/peers/add -Method POST -ContentType "application/json" -Body '{"address":"127.0.0.1","port":5002}' -UseBasicParsing

# Node2 connaît Node1 et Node3
Invoke-WebRequest -Uri http://127.0.0.1:5001/peers/add -Method POST -ContentType "application/json" -Body '{"address":"127.0.0.1","port":5000}' -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:5001/peers/add -Method POST -ContentType "application/json" -Body '{"address":"127.0.0.1","port":5002}' -UseBasicParsing

# Node3 connaît Node1 et Node2
Invoke-WebRequest -Uri http://127.0.0.1:5002/peers/add -Method POST -ContentType "application/json" -Body '{"address":"127.0.0.1","port":5000}' -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:5002/peers/add -Method POST -ContentType "application/json" -Body '{"address":"127.0.0.1","port":5001}' -UseBasicParsing
```

---

## Démonstration complète

### 1. Créer des wallets et envoyer une transaction
```bash
python demo.py
```

Le script `demo.py` :
- Crée deux wallets (Alice et Bob)
- Mine un bloc pour qu'Alice reçoive la récompense (10 coins)
- Alice envoie 5 coins à Bob (transaction signée)
- Mine un second bloc pour confirmer la transaction
- Affiche les soldes finaux

### 2. Miner un bloc manuellement
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:5000/mine -Method POST -ContentType "application/json" -Body '{}' -UseBasicParsing
```

### 3. Synchroniser la chaîne sur tous les nœuds
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:5001/sync -Method POST -ContentType "application/json" -Body '{}' -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:5002/sync -Method POST -ContentType "application/json" -Body '{}' -UseBasicParsing
```

### 4. Vérifier la propagation

Les 3 nœuds doivent avoir le même `chain_length` :
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:5000/status -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:5001/status -UseBasicParsing
Invoke-WebRequest -Uri http://127.0.0.1:5002/status -UseBasicParsing
```

### 5. Smart Contracts

#### Counter — incrémenter un compteur
```powershell
# Déployer
Invoke-WebRequest -Uri http://127.0.0.1:5000/contracts/deploy -Method POST -ContentType "application/json" -Body '{"type":"counter","id":"counter-1","owner":"0xABC"}' -UseBasicParsing

# Incrémenter
Invoke-WebRequest -Uri http://127.0.0.1:5000/transactions/new -Method POST -ContentType "application/json" -Body '{"sender":"0xABC","receiver":"counter-1","amount":0,"nonce":0,"data":{"action":"increment"},"signature":"","id":"tx-001"}' -UseBasicParsing

# Vérifier l'état
Invoke-WebRequest -Uri http://127.0.0.1:5000/contracts/counter-1 -UseBasicParsing
```

#### Escrow — dépôt conditionnel
```powershell
# Déployer
Invoke-WebRequest -Uri http://127.0.0.1:5000/contracts/deploy -Method POST -ContentType "application/json" -Body '{"type":"escrow","id":"escrow-1","owner":"0xABC","buyer":"0xBUYER","seller":"0xSELLER","amount":50.0}' -UseBasicParsing

# Vérifier l'état
Invoke-WebRequest -Uri http://127.0.0.1:5000/contracts/escrow-1 -UseBasicParsing
```

### 6. Vérifier un solde
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:5000/balance/<adresse> -UseBasicParsing
```

### 7. Consulter la chaîne complète
```powershell
Invoke-WebRequest -Uri http://127.0.0.1:5000/chain -UseBasicParsing
```

---

## Lancer les tests automatisés
```powershell
pytest tests/ -v
```

Les tests couvrent :
- `test_crypto.py` — hash, sign, verify, dérivation d'adresse
- `test_transaction.py` — signature, détection de falsification, sérialisation, nonce
- `test_blockchain.py` — genesis, minage, validation, détection de falsification, Merkle root
- `test_p2p.py` — ajout de peers, anti-doublon, anti-boucle, sérialisation
- `test_contracts.py` — counter, escrow, exécution déterministe

---

## Architecture
```
PythCoin/
├── src/
│   ├── crypto/
│   │   └── crypto_utils.py     # Hash SHA-256, sign/verify EC SECP256K1, dérivation adresse
│   ├── core/
│   │   ├── transaction.py      # Transaction signée avec nonce anti-rejeu
│   │   ├── block.py            # Bloc avec Merkle root et Proof of Work
│   │   ├── blockchain.py       # Chaîne de blocs avec validation complète
│   │   └── state.py            # WorldState — balances et états des contrats
│   ├── p2p/
│   │   ├── peer.py             # Représentation d'un pair distant
│   │   └── network.py          # Broadcast, anti-boucle, sync longest chain
│   ├── contracts/
│   │   ├── smart_contract.py   # Counter, Escrow, ConditionalTransfer
│   │   └── contract_engine.py  # Moteur d'exécution déterministe
│   └── wallet/
│       └── wallet.py           # Génération clés, signature transactions
├── node.py                     # Serveur Flask — API REST du nœud
├── demo.py                     # Script de démonstration complet
├── tests/                      # Tests pytest
├── conftest.py                 # Configuration pytest (résolution des imports)
├── requirements.txt
└── README.md
```

---

## Modèle de données

| Objet | Champs principaux |
|---|---|
| Transaction | sender, receiver, amount, nonce, signature, data |
| Block | index, timestamp, transactions, previous_hash, nonce, merkle_root, hash |
| Blockchain | chain (liste de blocs liés), difficulty |
| WorldState | balances (adresse → solde), contracts (id → état) |

---

## Sécurité

- **Signatures EC SECP256K1** — même courbe elliptique que Bitcoin
- **Prévention du rejeu** — nonce incrémenté par adresse
- **Proof of Work** — difficulté configurable (`--difficulty`)
- **Validation de chaîne** — hash + Merkle root + PoW vérifiés à chaque bloc
- **Anti-boucle P2P** — identifiant unique par message broadcasté
- **Règle de la chaîne la plus longue** — synchronisation automatique via `/sync`

---

## API REST

| Méthode | Route | Description |
|---|---|---|
| GET | `/status` | Statut du nœud |
| GET | `/chain` | Chaîne complète |
| GET | `/peers` | Liste des pairs |
| POST | `/peers/add` | Ajouter un pair |
| POST | `/mine` | Miner un bloc |
| POST | `/sync` | Synchroniser la chaîne |
| GET | `/balance/<address>` | Solde d'une adresse |
| POST | `/transactions/new` | Nouvelle transaction |
| POST | `/contracts/deploy` | Déployer un contrat |
| GET | `/contracts/<id>` | État d'un contrat |
| GET | `/state` | État global du monde |