import json
import time
from src.crypto.crypto_utils import CryptoUtils
from .transaction import Transaction


class Block:
    """Represents a block in the blockchain."""

    def __init__(self, index: int, transactions: list, previous_hash: str,
                 difficulty: int = 4):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.difficulty = difficulty
        self.merkle_root = self.compute_merkle_root()
        self.hash = self.compute_hash()

    def compute_merkle_root(self) -> str:
        """Compute simplified Merkle root from transaction hashes."""
        if not self.transactions:
            return CryptoUtils.hash("empty")

        hashes = [tx.compute_hash() if hasattr(tx, 'compute_hash')
                  else CryptoUtils.hash(json.dumps(tx))
                  for tx in self.transactions]

        while len(hashes) > 1:
            if len(hashes) % 2 != 0:
                hashes.append(hashes[-1])  # Duplicate last if odd number
            hashes = [
                CryptoUtils.hash(hashes[i] + hashes[i + 1])
                for i in range(0, len(hashes), 2)
            ]
        return hashes[0]

    def compute_hash(self) -> str:
        """Compute block hash."""
        block_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "merkle_root": self.merkle_root,
            "difficulty": self.difficulty,
        }
        return CryptoUtils.hash_dict(block_data)

    def mine(self) -> None:
        """Proof of Work: find nonce so hash starts with 'difficulty' zeros."""
        target = "0" * self.difficulty
        self.nonce = 0
        self.hash = self.compute_hash()
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.compute_hash()
        print(f"[PoW] Block #{self.index} mined! Nonce={self.nonce}, Hash={self.hash[:20]}...")

    def is_valid(self) -> bool:
        """Verify block integrity."""
        if self.compute_hash() != self.hash:
            return False
        if self.compute_merkle_root() != self.merkle_root:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": [
                tx.to_full_dict() if hasattr(tx, 'to_full_dict') else tx
                for tx in self.transactions
            ],
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "merkle_root": self.merkle_root,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Block":
        txs = [Transaction.from_dict(tx) for tx in data.get("transactions", [])]
        block = cls(
            index=data["index"],
            transactions=txs,
            previous_hash=data["previous_hash"],
            difficulty=data.get("difficulty", 4)
        )
        block.timestamp = data["timestamp"]
        block.nonce = data["nonce"]
        block.merkle_root = data["merkle_root"]
        block.hash = data["hash"]
        return block

    def __repr__(self):
        return f"Block(#{self.index}, hash={self.hash[:15]}..., txs={len(self.transactions)})"