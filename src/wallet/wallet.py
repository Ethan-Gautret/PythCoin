import json
from src.crypto.crypto_utils import CryptoUtils
from src.core.transaction import Transaction


class Wallet:
    """Manages a user's cryptographic identity and signs transactions."""

    def __init__(self):
        self._private_key = None
        self._public_key = None
        self.private_key_pem: str = ""
        self.public_key_pem: str = ""
        self.address: str = ""

    def generate_keys(self) -> None:
        """Generate a new EC key pair and derive the address."""
        self._private_key, self._public_key = CryptoUtils.generate_key_pair()
        self.private_key_pem = CryptoUtils.private_key_to_pem(self._private_key)
        self.public_key_pem = CryptoUtils.public_key_to_pem(self._public_key)
        self.address = CryptoUtils.derive_address(self.public_key_pem)
        print(f"[Wallet] New wallet created: {self.address}")

    def load_from_pem(self, private_key_pem: str) -> None:
        """Load a wallet from an existing PEM private key."""
        self._private_key = CryptoUtils.pem_to_private_key(private_key_pem)
        self._public_key = self._private_key.public_key()
        self.private_key_pem = private_key_pem
        self.public_key_pem = CryptoUtils.public_key_to_pem(self._public_key)
        self.address = CryptoUtils.derive_address(self.public_key_pem)

    def sign(self, data: str) -> str:
        """Sign arbitrary data."""
        if not self._private_key:
            raise ValueError("No private key loaded. Call generate_keys() first.")
        return CryptoUtils.sign(data, self._private_key)

    def create_transaction(self, receiver: str, amount: float,
                           nonce: int = 0, data: dict = None) -> Transaction:
        """Create and sign a transaction."""
        if not self._private_key:
            raise ValueError("No private key loaded.")
        tx = Transaction(
            sender=self.address,
            receiver=receiver,
            amount=amount,
            nonce=nonce,
            data=data or {}
        )
        tx.sign(self._private_key)
        return tx

    def verify_transaction(self, tx: Transaction) -> bool:
        """Verify a transaction signed by this wallet."""
        return tx.verify(self._public_key)

    def save_to_file(self, filepath: str) -> None:
        """Save wallet (private key) to a JSON file."""
        with open(filepath, "w") as f:
            json.dump({
                "address": self.address,
                "private_key_pem": self.private_key_pem,
                "public_key_pem": self.public_key_pem,
            }, f, indent=2)
        print(f"[Wallet] Saved to {filepath}")

    @classmethod
    def load_from_file(cls, filepath: str) -> "Wallet":
        """Load wallet from a JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        wallet = cls()
        wallet.load_from_pem(data["private_key_pem"])
        return wallet

    def __repr__(self):
        return f"Wallet(address={self.address})"