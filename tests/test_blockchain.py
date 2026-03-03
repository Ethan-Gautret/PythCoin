import pytest
from src.core.blockchain import Blockchain
from src.core.block import Block
from src.wallet.wallet import Wallet


def test_genesis_block():
    bc = Blockchain(difficulty=2)
    assert len(bc) == 1
    assert bc.chain[0].previous_hash == "0" * 64

def test_mine_and_add_block():
    bc = Blockchain(difficulty=2)
    wallet = Wallet()
    wallet.generate_keys()
    tx = wallet.create_transaction("0xreceiver", 5.0)
    block = bc.mine_block([tx], miner_address=wallet.address)
    assert bc.add_block(block)
    assert len(bc) == 2

def test_chain_validation():
    bc = Blockchain(difficulty=2)
    wallet = Wallet()
    wallet.generate_keys()
    block = bc.mine_block([], miner_address=wallet.address)
    bc.add_block(block)
    assert bc.validate_chain()

def test_chain_tamper_detection():
    bc = Blockchain(difficulty=2)
    wallet = Wallet()
    wallet.generate_keys()
    block = bc.mine_block([], miner_address=wallet.address)
    bc.add_block(block)
    # Tamper with genesis block
    bc.chain[0].transactions = []
    bc.chain[0].hash = "tampered"
    assert not bc.validate_chain()

def test_block_chaining():
    bc = Blockchain(difficulty=2)
    wallet = Wallet()
    wallet.generate_keys()
    for i in range(3):
        block = bc.mine_block([], miner_address=wallet.address)
        bc.add_block(block)
    for i in range(1, len(bc.chain)):
        assert bc.chain[i].previous_hash == bc.chain[i-1].hash

def test_merkle_root():
    bc = Blockchain(difficulty=2)
    wallet = Wallet()
    wallet.generate_keys()
    tx1 = wallet.create_transaction("0xA", 1.0)
    tx2 = wallet.create_transaction("0xB", 2.0)
    block = bc.mine_block([tx1, tx2], miner_address=wallet.address)
    assert block.merkle_root != ""
    original_root = block.merkle_root
    block.transactions[0].amount = 999.0
    assert block.compute_merkle_root() != original_root