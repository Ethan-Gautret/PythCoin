import json
import uuid
from src.crypto.crypto_utils import CryptoUtils


class Transaction:
    """Represents a blockchain transaction."""

    def __init__(self, sender: str, receiver: str, amount: float,
                 nonce: int = 0, data: dict = None):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.nonce = nonce           # Replay attack prevention
        self.data = data or {}       # Optional: smart contract call data
        self.signature = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "nonce": self.nonce,
            "data": self.data,
        }

    def compute_hash(self) -> str:
        """Compute transaction hash (without signature, for signing)."""
        return CryptoUtils.hash_dict(self.to_dict())

    def sign(self, private_key) -> None:
        """Sign the transaction with sender's private key."""
        tx_hash = self.compute_hash()
        self.signature = CryptoUtils.sign(tx_hash, private_key)

    def verify(self, public_key) -> bool:
        """Verify the transaction signature."""
        if not self.signature:
            return False
        tx_hash = self.compute_hash()
        return CryptoUtils.verify(tx_hash, self.signature, public_key)

    def is_valid(self) -> bool:
        """Basic validity check (non-negative amount, required fields)."""
        if self.amount < 0:
            return False
        if not self.sender or not self.receiver:
            return False
        return True

    def to_full_dict(self) -> dict:
        """Full dict including signature (for serialization)."""
        d = self.to_dict()
        d["signature"] = self.signature
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        tx = cls(
            sender=data["sender"],
            receiver=data["receiver"],
            amount=data["amount"],
            nonce=data.get("nonce", 0),
            data=data.get("data", {})
        )
        tx.id = data.get("id", tx.id)
        tx.signature = data.get("signature", "")
        return tx

    def __repr__(self):
        return f"Transaction({self.sender[:10]}... -> {self.receiver[:10]}..., {self.amount})"