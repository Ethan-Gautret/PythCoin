import pytest
from src.crypto.crypto_utils import CryptoUtils


def test_hash_deterministic():
    assert CryptoUtils.hash("hello") == CryptoUtils.hash("hello")

def test_hash_different_inputs():
    assert CryptoUtils.hash("hello") != CryptoUtils.hash("world")

def test_hash_avalanche():
    h1 = CryptoUtils.hash("hello")
    h2 = CryptoUtils.hash("hellO")
    assert h1 != h2

def test_sign_verify():
    priv, pub = CryptoUtils.generate_key_pair()
    data = "test data"
    sig = CryptoUtils.sign(data, priv)
    assert CryptoUtils.verify(data, sig, pub)

def test_verify_tampered_data():
    priv, pub = CryptoUtils.generate_key_pair()
    sig = CryptoUtils.sign("original", priv)
    assert not CryptoUtils.verify("tampered", sig, pub)

def test_address_derivation():
    priv, pub = CryptoUtils.generate_key_pair()
    pub_pem = CryptoUtils.public_key_to_pem(pub)
    addr = CryptoUtils.derive_address(pub_pem)
    assert addr.startswith("0x")
    assert len(addr) == 42

def test_pem_roundtrip():
    priv, pub = CryptoUtils.generate_key_pair()
    priv_pem = CryptoUtils.private_key_to_pem(priv)
    pub_pem = CryptoUtils.public_key_to_pem(pub)
    priv2 = CryptoUtils.pem_to_private_key(priv_pem)
    pub2 = CryptoUtils.pem_to_public_key(pub_pem)
    # Re-sign and verify
    sig = CryptoUtils.sign("data", priv2)
    assert CryptoUtils.verify("data", sig, pub2)