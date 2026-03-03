class WorldState:
    """Maintains the current world state: balances and contract states."""

    def __init__(self):
        self.balances: dict[str, float] = {}
        self.contracts: dict[str, dict] = {}

    def update_balance(self, address: str, amount: float) -> None:
        """Update balance for an address (can be negative for deductions)."""
        if address not in self.balances:
            self.balances[address] = 0.0
        self.balances[address] += amount

    def get_balance(self, address: str) -> float:
        return self.balances.get(address, 0.0)

    def set_contract_state(self, contract_id: str, state: dict) -> None:
        self.contracts[contract_id] = state

    def get_contract_state(self, contract_id: str) -> dict:
        return self.contracts.get(contract_id, {})

    def apply_transaction(self, tx) -> bool:
        """Apply a transaction to the world state."""
        if tx.sender == "COINBASE":
            self.update_balance(tx.receiver, tx.amount)
            return True

        sender_balance = self.get_balance(tx.sender)
        if sender_balance < tx.amount:
            print(f"[State] Insufficient balance for {tx.sender[:12]}...")
            return False

        self.update_balance(tx.sender, -tx.amount)
        self.update_balance(tx.receiver, tx.amount)
        return True

    def apply_block(self, block) -> None:
        """Apply all transactions in a block to the world state."""
        for tx in block.transactions:
            self.apply_transaction(tx)

    def rebuild_from_blockchain(self, blockchain) -> None:
        """Rebuild state from scratch by replaying the entire chain."""
        self.balances = {}
        self.contracts = {}
        for block in blockchain.chain:
            self.apply_block(block)

    def to_dict(self) -> dict:
        return {
            "balances": self.balances,
            "contracts": self.contracts
        }

    def __repr__(self):
        return f"WorldState(accounts={len(self.balances)}, contracts={len(self.contracts)})"