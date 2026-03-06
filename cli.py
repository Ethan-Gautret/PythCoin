"""
PythCoin — Interface CLI interactive
"""
import requests
import json
import sys
import os

BASE_URL = "http://127.0.0.1:5000"


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def set_node():
    global BASE_URL
    url = input(f"URL du nœud [{BASE_URL}] : ").strip()
    if url:
        BASE_URL = url
    print(f"✅ Nœud : {BASE_URL}")


def api(method, path, body=None):
    try:
        url = BASE_URL + path
        headers = {"Content-Type": "application/json"}
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=5)
        else:
            r = requests.post(url, headers=headers, json=body, timeout=10)
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": f"Impossible de joindre {BASE_URL}"}
    except Exception as e:
        return {"error": str(e)}


def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def print_separator():
    print("─" * 50)


def print_header():
    clear()
    print("=" * 50)
    print("  🪙  PythCoin — Interface CLI")
    print(f"  Nœud : {BASE_URL}")
    print("=" * 50)


# ─── STATUT ───────────────────────────────────────

def status():
    print_header()
    print("\n📊 STATUT DU NŒUD\n")
    data = api("GET", "/status")
    if "error" in data:
        print(f"❌ {data['error']}")
    else:
        print(f"  Nom       : {data.get('node', '—')}")
        print(f"  Adresse   : {data.get('address', '—')}")
        print(f"  Chaîne    : {data.get('chain_length', '—')} blocs")
        print(f"  Mempool   : {data.get('mempool_size', '—')} transactions")
        print(f"  Pairs     : {data.get('peers', '—')}")
    input("\nAppuyez sur Entrée pour continuer...")


# ─── BLOCKCHAIN ───────────────────────────────────

def show_chain():
    print_header()
    print("\n⛓️  BLOCKCHAIN\n")
    data = api("GET", "/chain")
    if "error" in data:
        print(f"❌ {data['error']}")
    else:
        chain = list(reversed(data.get("chain", [])))
        print(f"  Longueur : {data.get('length', 0)} blocs\n")
        for block in chain:
            print(f"  ┌─ Bloc #{block['index']}")
            print(f"  │  Hash     : {block['hash'][:30]}...")
            print(f"  │  Prev     : {block['previous_hash'][:30]}...")
            print(f"  │  Nonce    : {block['nonce']}")
            print(f"  │  Tx       : {len(block.get('transactions', []))}")
            print(f"  └─ Merkle  : {block.get('merkle_root', '')[:30]}...")
            print()
    input("Appuyez sur Entrée pour continuer...")


# ─── MINAGE ───────────────────────────────────────

def mine():
    print_header()
    print("\n⛏️  MINER UN BLOC\n")
    miner = input("  Adresse du mineur (laisser vide = nœud) : ").strip()
    body = {"miner_address": miner} if miner else {}
    print("\n  ⏳ Minage en cours...")
    data = api("POST", "/mine", body)
    if data.get("success"):
        block = data["block"]
        print(f"\n  ✅ Bloc #{block['index']} miné !")
        print(f"  Hash  : {block['hash']}")
        print(f"  Nonce : {block['nonce']}")
    else:
        print(f"\n  ❌ {data.get('message', 'Erreur')}")
    input("\nAppuyez sur Entrée pour continuer...")


# ─── TRANSACTIONS ─────────────────────────────────

def new_transaction():
    print_header()
    print("\n💸 NOUVELLE TRANSACTION\n")
    sender   = input("  Sender   : ").strip()
    receiver = input("  Receiver : ").strip()
    amount   = float(input("  Montant  : ").strip() or "0")
    nonce    = int(input("  Nonce    : ").strip() or "0")
    data_raw = input("  Data JSON (vide si aucun) : ").strip()
    data_field = {}
    if data_raw:
        try:
            data_field = json.loads(data_raw)
        except:
            print("  ⚠️ JSON invalide, data ignorée")

    body = {
        "id": f"tx-cli-{nonce}-{sender[:6]}",
        "sender": sender,
        "receiver": receiver,
        "amount": amount,
        "nonce": nonce,
        "data": data_field,
        "signature": "",
    }
    data = api("POST", "/transactions/new", body)
    if data.get("success"):
        print(f"\n  ✅ Transaction acceptée !")
    else:
        print(f"\n  ❌ {data.get('message', 'Erreur')}")
    input("\nAppuyez sur Entrée pour continuer...")


# ─── SOLDE ────────────────────────────────────────

def check_balance():
    print_header()
    print("\n💰 SOLDE D'UNE ADRESSE\n")
    address = input("  Adresse : ").strip()
    if not address:
        print("  ❌ Adresse vide")
    else:
        data = api("GET", f"/balance/{address}")
        if "error" in data:
            print(f"  ❌ {data['error']}")
        else:
            print(f"\n  Adresse : {data.get('address')}")
            print(f"  Solde   : {data.get('balance')} coins")
    input("\nAppuyez sur Entrée pour continuer...")


# ─── PEERS ────────────────────────────────────────

def manage_peers():
    print_header()
    print("\n🌐 RÉSEAU P2P\n")

    data = api("GET", "/peers")
    peers = data.get("peers", [])
    if not peers:
        print("  Aucun pair connu.\n")
    else:
        print(f"  {len(peers)} pair(s) connu(s) :\n")
        for p in peers:
            print(f"  🟢 {p['address']}:{p['port']}")

    print_separator()
    print("\n  [1] Ajouter un pair")
    print("  [0] Retour")
    choice = input("\n  Choix : ").strip()

    if choice == "1":
        addr = input("  Adresse : ").strip() or "127.0.0.1"
        port = int(input("  Port    : ").strip() or "5001")
        result = api("POST", "/peers/add", {"address": addr, "port": port})
        if result.get("success"):
            print(f"  ✅ Pair ajouté ! ({result['peers']} pairs)")
        else:
            print(f"  ⚠️ Déjà connu ({result.get('peers', '?')} pairs)")
        input("\nAppuyez sur Entrée pour continuer...")


# ─── SYNC ─────────────────────────────────────────

def sync():
    print_header()
    print("\n🔄 SYNCHRONISATION\n")
    print("  ⏳ Synchronisation en cours...")
    data = api("POST", "/sync", {})
    if "error" in data:
        print(f"  ❌ {data['error']}")
    else:
        print(f"  ✅ Chaîne synchronisée : {data.get('chain_length')} blocs")
    input("\nAppuyez sur Entrée pour continuer...")


# ─── SMART CONTRACTS ──────────────────────────────

def smart_contracts():
    while True:
        print_header()
        print("\n📜 SMART CONTRACTS\n")
        print("  [1] Déployer un contrat")
        print("  [2] Appeler un contrat")
        print("  [3] Lire l'état d'un contrat")
        print("  [0] Retour")
        choice = input("\n  Choix : ").strip()

        if choice == "1":
            deploy_contract()
        elif choice == "2":
            call_contract()
        elif choice == "3":
            read_contract()
        elif choice == "0":
            break


def deploy_contract():
    print_header()
    print("\n🚀 DÉPLOYER UN CONTRAT\n")
    print("  Types : counter / escrow / conditional_transfer")
    ctype  = input("  Type    : ").strip()
    cid    = input("  ID      : ").strip()
    owner  = input("  Owner   : ").strip()
    body   = {"type": ctype, "id": cid, "owner": owner}

    if ctype == "escrow":
        body["buyer"]  = input("  Buyer   : ").strip()
        body["seller"] = input("  Seller  : ").strip()
        body["amount"] = float(input("  Montant : ").strip() or "50")
    elif ctype == "conditional_transfer":
        body["sender"]   = input("  Sender   : ").strip()
        body["receiver"] = input("  Receiver : ").strip()
        body["amount"]   = float(input("  Montant  : ").strip() or "100")
        body["required_approvals"] = int(input("  Approbations requises : ").strip() or "2")

    data = api("POST", "/contracts/deploy", body)
    if data.get("success"):
        print(f"\n  ✅ Contrat déployé : {data['contract_id']}")
    else:
        print(f"\n  ❌ {data.get('message', 'Erreur')}")
    input("\nAppuyez sur Entrée pour continuer...")


def call_contract():
    print_header()
    print("\n▶️  APPELER UN CONTRAT\n")
    contract_id = input("  ID du contrat : ").strip()
    sender      = input("  Sender        : ").strip()
    nonce       = int(input("  Nonce         : ").strip() or "0")
    data_raw    = input("  Action JSON   : ").strip()
    data_field  = {}
    if data_raw:
        try:
            data_field = json.loads(data_raw)
        except:
            print("  ⚠️ JSON invalide")

    body = {
        "id": f"tx-contract-{nonce}",
        "sender": sender,
        "receiver": contract_id,
        "amount": 0,
        "nonce": nonce,
        "data": data_field,
        "signature": "",
    }
    data = api("POST", "/transactions/new", body)
    if data.get("success"):
        print(f"\n  ✅ Contrat exécuté !")
    else:
        print(f"\n  ❌ {data.get('message', 'Erreur')}")
    input("\nAppuyez sur Entrée pour continuer...")


def read_contract():
    print_header()
    print("\n🔍 ÉTAT D'UN CONTRAT\n")
    contract_id = input("  ID du contrat : ").strip()
    data = api("GET", f"/contracts/{contract_id}")
    if "error" in data:
        print(f"  ❌ {data['error']}")
    else:
        print(f"\n  Contrat : {data.get('contract_id')}")
        print(f"  État    :")
        print_json(data.get("state", {}))
    input("\nAppuyez sur Entrée pour continuer...")


# ─── ÉTAT GLOBAL ──────────────────────────────────

def world_state():
    print_header()
    print("\n🗂️  ÉTAT GLOBAL (WorldState)\n")
    data = api("GET", "/state")
    if "error" in data:
        print(f"  ❌ {data['error']}")
    else:
        balances = data.get("balances", {})
        contracts = data.get("contracts", {})
        print(f"  💰 Balances ({len(balances)}) :")
        for addr, bal in balances.items():
            print(f"     {addr[:20]}... : {bal} coins")
        print(f"\n  📜 Contrats ({len(contracts)}) :")
        for cid, state in contracts.items():
            print(f"     {cid} : {state}")
    input("\nAppuyez sur Entrée pour continuer...")

# ─── WALLET ───────────────────────────────────────

def create_wallet():
    print_header()
    print("\n👛 CRÉER UN WALLET\n")
    from src.wallet.wallet import Wallet
    import os

    wallet = Wallet()
    wallet.generate_keys()

    print(f"\n  ✅ Wallet créé !\n")
    print(f"  Adresse    : {wallet.address}")
    print(f"  Clé pub    : {wallet.public_key_pem[:40]}...")
    print(f"  Clé privée : {wallet.private_key_pem[:40]}...")

    print_separator()
    save = input("\n  Sauvegarder dans un fichier ? (o/n) : ").strip().lower()
    if save == "o":
        filename = input("  Nom du fichier [wallet.json] : ").strip() or "wallet.json"
        wallet.save_to_file(filename)
        print(f"  ✅ Sauvegardé dans {filename}")

    input("\nAppuyez sur Entrée pour continuer...")
# ─── MENU PRINCIPAL ───────────────────────────────

def main():
    while True:
        print_header()
        print()
        print("  [1]  📊  Statut du nœud")
        print("  [2]  ⛓️   Voir la blockchain")
        print("  [3]  ⛏️   Miner un bloc")
        print("  [4]  💸  Nouvelle transaction")
        print("  [5]  💰  Consulter un solde")
        print("  [6]  🌐  Gérer les pairs P2P")
        print("  [7]  🔄  Synchroniser la chaîne")
        print("  [8]  📜  Smart Contracts")
        print("  [9]  🗂️   État global")
        print("  [w]  👛  Créer un wallet")  # ← ajouter cette ligne
        print("  [c]  ⚙️   Changer de nœud")
        print("  [q]  ❌  Quitter")
        print()
        print_separator()
        choice = input("  Choix : ").strip().lower()

        if   choice == "1": status()
        elif choice == "2": show_chain()
        elif choice == "3": mine()
        elif choice == "4": new_transaction()
        elif choice == "5": check_balance()
        elif choice == "6": manage_peers()
        elif choice == "7": sync()
        elif choice == "8": smart_contracts()
        elif choice == "9": world_state()
        elif choice == "w": create_wallet()  # ← ajouter cette ligne
        elif choice == "c": set_node()
        elif choice == "q":
            print("\n  👋 Au revoir !\n")
            sys.exit(0)


if __name__ == "__main__":
    main()