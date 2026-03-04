"""
Main node — Flask HTTP server exposing the blockchain API.
Each running instance = one node in the P2P network.
"""
import argparse
import json
import threading
import time
from flask import Flask, request, jsonify

from src.crypto.crypto_utils import CryptoUtils
from src.core.transaction import Transaction
from src.core.block import Block
from src.core.blockchain import Blockchain
from src.core.state import WorldState
from src.wallet.wallet import Wallet
from src.p2p.peer import Peer
from src.p2p.network import P2PNetwork
from src.contracts.contract_engine import ContractEngine


class Node:
    """Full blockchain node with P2P networking."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5000,
                 difficulty: int = 3, node_name: str = "Node"):
        self.host = host
        self.port = port
        self.node_name = node_name

        # Core components
        self.blockchain = Blockchain(difficulty=difficulty)
        self.world_state = WorldState()
        self.contract_engine = ContractEngine(self.world_state)
        self.p2p = P2PNetwork(host, port)
        self.mempool: list[Transaction] = []

        # Mining wallet
        self.wallet = Wallet()
        self.wallet.generate_keys()

        # Nonce tracker per address (replay attack prevention)
        self._nonces: dict[str, int] = {}

        # Flask app
        self.app = Flask(node_name)
        self._register_routes()

        # Rebuild state from genesis
        self.world_state.rebuild_from_blockchain(self.blockchain)

        print(f"\n{'='*50}")
        print(f"  Node: {self.node_name}")
        print(f"  Address: {self.wallet.address}")
        print(f"  Port: {self.port}")
        print(f"{'='*50}\n")

    def _register_routes(self):
        app = self.app

        @app.route("/status", methods=["GET"])
        def status():
            return jsonify({
                "node": self.node_name,
                "address": self.wallet.address,
                "chain_length": len(self.blockchain),
                "mempool_size": len(self.mempool),
                "peers": len(self.p2p.peers),
            })

        @app.route("/chain", methods=["GET"])
        def get_chain():
            return jsonify({
                "length": len(self.blockchain),
                "chain": self.blockchain.to_dict()["chain"]
            })

        @app.route("/peers", methods=["GET"])
        def get_peers():
            return jsonify(self.p2p.to_dict())

        @app.route("/peers/add", methods=["POST"])
        def add_peer():
            data = request.json
            peer = Peer(data["address"], data["port"])
            added = self.p2p.add_peer(peer)
            # Also discover their peers
            if added:
                self.p2p.discover_peers(peer)
                self._sync_chain()
            return jsonify({"success": added, "peers": len(self.p2p.peers)})

        @app.route("/transactions/new", methods=["POST"])
        def new_transaction():
            """Create a new transaction (from external wallet data)."""
            data = request.json
            tx = Transaction.from_dict(data)

            success, msg = self.add_transaction(tx, data.get("public_key_pem", ""))
            return jsonify({"success": success, "message": msg})

        @app.route("/transactions/receive", methods=["POST"])
        def receive_transaction():
            """Receive a broadcast transaction from a peer."""
            data = request.json
            tx = Transaction.from_dict(data)
            pub_key_pem = data.get("public_key_pem", "")

            # Check not already in mempool
            if any(t.id == tx.id for t in self.mempool):
                return jsonify({"success": False, "message": "Already known"})

            success, msg = self.add_transaction(tx, pub_key_pem, broadcast=False)
            return jsonify({"success": success, "message": msg})

        # @app.route("/mine", methods=["POST"])
        # def mine():
        #     """Mine a new block from the current mempool."""
        #     if not self.mempool:
        #         return jsonify({"success": False, "message": "Mempool is empty"})
        #     block = self.mine_block()
        #     if block:
        #         return jsonify({"success": True, "block": block.to_dict()})
        #     return jsonify({"success": False, "message": "Mining failed"})

        @app.route("/mine", methods=["POST"])
        def mine():
            data = request.json or {}
            miner_addr = data.get("miner_address", self.wallet.address)

            txs = list(self.mempool)
            self.mempool.clear()

            block = self.blockchain.mine_block(txs, miner_address=miner_addr)
            if self.blockchain.add_block(block):
                self.world_state.apply_block(block)
                self.p2p.broadcast_block(block.to_dict())
                print(f"[Node] Block mined and broadcast: #{block.index}")
                return jsonify({"success": True, "block": block.to_dict()})
            return jsonify({"success": False, "message": "Mining failed"})

        @app.route("/blocks/receive", methods=["POST"])
        def receive_block():
            """Receive a broadcast block from a peer."""
            data = request.json
            block = Block.from_dict(data)
            added = self._add_received_block(block)
            return jsonify({"success": added})

        @app.route("/state", methods=["GET"])
        def get_state():
            return jsonify(self.world_state.to_dict())

        @app.route("/balance/<address>", methods=["GET"])
        def get_balance(address):
            balance = self.world_state.get_balance(address)
            return jsonify({"address": address, "balance": balance})

        @app.route("/contracts/deploy", methods=["POST"])
        def deploy_contract():
            data = request.json
            ctype = data.get("type")
            if ctype == "counter":
                c = self.contract_engine.create_counter(data["id"], data["owner"])
                return jsonify({"success": True, "contract_id": c.contract_id})
            elif ctype == "escrow":
                c = self.contract_engine.create_escrow(
                    data["id"], data["owner"],
                    data["buyer"], data["seller"], data["amount"]
                )
                return jsonify({"success": True, "contract_id": c.contract_id})
            elif ctype == "conditional_transfer":
                c = self.contract_engine.create_conditional_transfer(
                    data["id"], data["owner"],
                    data["sender"], data["receiver"],
                    data["amount"], data.get("required_approvals", 2)
                )
                return jsonify({"success": True, "contract_id": c.contract_id})
            return jsonify({"success": False, "message": "Unknown contract type"})

        @app.route("/contracts/<contract_id>", methods=["GET"])
        def contract_state(contract_id):
            state = self.world_state.get_contract_state(contract_id)
            return jsonify({"contract_id": contract_id, "state": state})

        @app.route("/sync", methods=["POST"])
        def sync():
            self._sync_chain()
            return jsonify({"success": True, "chain_length": len(self.blockchain)})

    def add_transaction(self, tx: Transaction, public_key_pem: str = "",
                        broadcast: bool = True) -> tuple[bool, str]:
        """Validate and add a transaction to the mempool."""
        # Validate signature (if public key provided)
        if public_key_pem and tx.sender != "COINBASE":
            try:
                pub_key = CryptoUtils.pem_to_public_key(public_key_pem)
                if not tx.verify(pub_key):
                    return False, "Invalid signature"
            except Exception as e:
                return False, f"Signature verification error: {e}"

        # Replay attack check via nonce
        expected_nonce = self._nonces.get(tx.sender, 0)
        if tx.nonce < expected_nonce:
            return False, f"Nonce too low (expected >= {expected_nonce})"

        # Check if it's a contract call
        if tx.receiver in self.contract_engine._contracts:
            result = self.contract_engine.run(tx)
            if not result:
                return False, "Contract execution failed"
        else:
            # Basic balance check
            if tx.sender != "COINBASE":
                balance = self.world_state.get_balance(tx.sender)
                if balance < tx.amount:
                    return False, f"Insufficient balance ({balance} < {tx.amount})"

        self.mempool.append(tx)
        self._nonces[tx.sender] = tx.nonce + 1
        print(f"[Mempool] Transaction added: {tx.id[:8]}...")

        if broadcast:
            tx_data = tx.to_full_dict()
            tx_data["public_key_pem"] = public_key_pem
            self.p2p.broadcast_transaction(tx_data)

        return True, "Transaction accepted"

    def mine_block(self) -> Block | None:
        """Mine a block and add it to the chain."""
        txs = list(self.mempool)
        self.mempool.clear()

        block = self.blockchain.mine_block(txs, miner_address=self.wallet.address)
        if self.blockchain.add_block(block):
            self.world_state.apply_block(block)
            self.p2p.broadcast_block(block.to_dict())
            print(f"[Node] Block mined and broadcast: #{block.index}")
            return block
        return None

    def _add_received_block(self, block: Block) -> bool:
        """Validate and add a block received from a peer."""
        if any(b.hash == block.hash for b in self.blockchain.chain):
            return False  # Already known

        added = self.blockchain.add_block(block)
        if added:
            self.world_state.apply_block(block)
            # Remove block transactions from mempool
            block_tx_ids = {tx.id for tx in block.transactions}
            self.mempool = [tx for tx in self.mempool if tx.id not in block_tx_ids]
            # Re-broadcast to other peers
            self.p2p.broadcast_block(block.to_dict())
            print(f"[Node] Received and added block #{block.index}")
        return added

    def _sync_chain(self) -> None:
        """Sync chain with the network (longest chain rule)."""
        best = self.p2p.get_longest_chain()
        if not best:
            print("[Sync] No chain received from peers")
            return

        print(f"[Sync] Best chain length from peers: {best.get('length', 0)}, local: {len(self.blockchain)}")

        if best.get("length", 0) > len(self.blockchain):
            try:
                candidate = Blockchain.from_dict({
                    "difficulty": self.blockchain.difficulty,
                    "chain": best["chain"]
                })
                if candidate.validate_chain():
                    self.blockchain = candidate
                    self.world_state.rebuild_from_blockchain(self.blockchain)
                    print(f"[Sync] Chain updated to length {len(self.blockchain)}")
                else:
                    print("[Sync] Candidate chain is invalid")
            except Exception as e:
                print(f"[Sync] Failed: {e}")
        else:
            print("[Sync] Already up to date")
    def start(self) -> None:
        """Start the Flask server."""
        self.app.run(host=self.host, port=self.port, debug=False)


def main():
    parser = argparse.ArgumentParser(description="Blockchain Node")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--difficulty", type=int, default=3)
    parser.add_argument("--name", default="Node")
    parser.add_argument("--peer", help="Bootstrap peer (host:port)", default=None)
    args = parser.parse_args()

    node = Node(host=args.host, port=args.port,
                difficulty=args.difficulty, node_name=args.name)

    if args.peer:
        host, port = args.peer.split(":")
        bootstrap = Peer(host, int(port))
        node.p2p.add_peer(bootstrap)
        node.p2p.discover_peers(bootstrap)
        node._sync_chain()

    node.start()


if __name__ == "__main__":
    main()