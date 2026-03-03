import pytest
from src.core.state import WorldState
from src.core.transaction import Transaction
from src.contracts.contract_engine import ContractEngine
from src.wallet.wallet import Wallet


def setup_engine():
    state = WorldState()
    engine = ContractEngine(state)
    return state, engine


def test_counter_contract():
    state, engine = setup_engine()
    wallet = Wallet()
    wallet.generate_keys()
    engine.create_counter("counter-1", wallet.address)

    tx = Transaction(sender=wallet.address, receiver="counter-1",
                     amount=0, data={"action": "increment"})
    assert engine.run(tx)
    contract_state = state.get_contract_state("counter-1")
    assert contract_state["count"] == 1

def test_counter_increment_multiple():
    state, engine = setup_engine()
    wallet = Wallet()
    wallet.generate_keys()
    engine.create_counter("counter-2", wallet.address)
    for _ in range(5):
        tx = Transaction(sender=wallet.address, receiver="counter-2",
                         amount=0, data={"action": "increment"})
        engine.run(tx)
    assert state.get_contract_state("counter-2")["count"] == 5

def test_escrow_flow():
    state, engine = setup_engine()
    owner = Wallet(); owner.generate_keys()
    buyer = Wallet(); buyer.generate_keys()
    seller = Wallet(); seller.generate_keys()

    state.update_balance(buyer.address, 100.0)
    engine.create_escrow("escrow-1", owner.address,
                         buyer.address, seller.address, 50.0)

    # Fund
    tx_fund = Transaction(sender=buyer.address, receiver="escrow-1",
                          amount=0, data={"action": "fund"})
    assert engine.run(tx_fund)
    assert state.get_balance(buyer.address) == 50.0

    # Release
    tx_release = Transaction(sender=seller.address, receiver="escrow-1",
                              amount=0, data={"action": "release"})
    assert engine.run(tx_release)
    assert state.get_balance(seller.address) == 50.0

def test_deterministic_execution():
    """Same contract + same transactions = same final state."""
    def run_scenario():
        state = WorldState()
        engine = ContractEngine(state)
        wallet = Wallet()
        wallet.generate_keys()
        engine.create_counter("det-counter", wallet.address)
        for _ in range(3):
            tx = Transaction(sender=wallet.address, receiver="det-counter",
                             amount=0, data={"action": "increment"})
            engine.run(tx)
        return state.get_contract_state("det-counter")["count"]

    assert run_scenario() == run_scenario() == 3