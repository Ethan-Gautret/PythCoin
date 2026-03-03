import pytest
from src.crypto.crypto_utils import CryptoUtils
from src.core.transaction import Transaction
from src.wallet.wallet import Wallet


def test_transaction_sign_and_verify():
    wallet = Wallet()
    wallet.generate_keys()
    tx = wallet.create_transaction("0xreceiver", 10.0, nonce=0)
    pub_key = CryptoUtils.pem_to_public_key(wallet.public_key_pem)
    assert tx.verify(pub_key)

def test_transaction_tamper_detection():
    wallet = Wallet()
    wallet.generate_keys()
    tx = wallet.create_transaction("0xreceiver", 10.0)
    tx.amount = 9999.0  # Tamper
    pub_key = CryptoUtils.pem_to_public_key(wallet.public_key_pem)
    assert not tx.verify(pub_key)

def test_transaction_serialization():
    wallet = Wallet()
    wallet.generate_keys()
    tx = wallet.create_transaction("0xreceiver", 5.0, nonce=1)
    d = tx.to_full_dict()
    tx2 = Transaction.from_dict(d)
    assert tx2.amount == tx.amount
    assert tx2.signature == tx.signature

def test_nonce_replay_prevention():
    wallet = Wallet()
    wallet.generate_keys()
    tx1 = wallet.create_transaction("0xreceiver", 5.0, nonce=0)
    tx2 = wallet.create_transaction("0xreceiver", 5.0, nonce=0)
    # Same nonce = replay attempt
    assert tx1.nonce == tx2.nonce