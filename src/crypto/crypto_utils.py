import hashlib
import json
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import base64


class CryptoUtils:
    """Utility class for cryptographic operations."""

    @staticmethod
    def hash(data: str) -> str:
        """Compute SHA-256 hash of a string."""
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def hash_dict(data: dict) -> str:
        """Compute SHA-256 hash of a dictionary (sorted keys for determinism)."""
        serialized = json.dumps(data, sort_keys=True)
        return CryptoUtils.hash(serialized)

    @staticmethod
    def generate_key_pair():
        """Generate an EC private/public key pair."""
        private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def private_key_to_pem(private_key) -> str:
        """Serialize private key to PEM string."""
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

    @staticmethod
    def public_key_to_pem(public_key) -> str:
        """Serialize public key to PEM string."""
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

    @staticmethod
    def pem_to_private_key(pem: str):
        """Load private key from PEM string."""
        return serialization.load_pem_private_key(
            pem.encode(), password=None, backend=default_backend()
        )

    @staticmethod
    def pem_to_public_key(pem: str):
        """Load public key from PEM string."""
        return serialization.load_pem_public_key(pem.encode(), backend=default_backend())

    @staticmethod
    def derive_address(public_key_pem: str) -> str:
        """Derive a blockchain address from a public key (SHA-256 of public key)."""
        return "0x" + hashlib.sha256(public_key_pem.encode()).hexdigest()[:40]

    @staticmethod
    def sign(data: str, private_key) -> str:
        """Sign data with a private key, return base64-encoded signature."""
        signature = private_key.sign(
            data.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        return base64.b64encode(signature).decode()

    @staticmethod
    def verify(data: str, signature: str, public_key) -> bool:
        """Verify a signature with a public key."""
        try:
            sig_bytes = base64.b64decode(signature.encode())
            public_key.verify(sig_bytes, data.encode(), ec.ECDSA(hashes.SHA256()))
            return True
        except (InvalidSignature, Exception):
            return False