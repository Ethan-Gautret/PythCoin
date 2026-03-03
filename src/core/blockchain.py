from .block import Block
from .transaction import Transaction


class Blockchain:
    """The main blockchain — a linked list of blocks."""

    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty
        self.chain: list[Block] = []
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        genesis = Block(
            index=0,
            transactions=[],
            previous_hash="0" * 64,
            difficulty=self.difficulty
        )
        genesis.mine()
        self.chain.append(genesis)
        print(f"[Genesis] Genesis block created: {genesis.hash[:20]}...")

    def get_last_block(self) -> Block:
        return self.chain[-1]

    def add_block(self, block: Block) -> bool:
        """Add a pre-validated block to the chain."""
        last = self.get_last_block()
        if block.previous_hash != last.hash:
            print(f"[Error] Block rejected: previous_hash mismatch")
            return False
        if not block.is_valid():
            print(f"[Error] Block rejected: invalid block")
            return False
        # Verify PoW
        if not block.hash.startswith("0" * self.difficulty):
            print(f"[Error] Block rejected: insufficient PoW")
            return False
        self.chain.append(block)
        return True

    def mine_block(self, transactions: list, miner_address: str = "NETWORK") -> Block:
        """Create and mine a new block from pending transactions."""
        # Add coinbase reward transaction
        reward_tx = Transaction(
            sender="COINBASE",
            receiver=miner_address,
            amount=10.0,
            nonce=0
        )
        all_txs = [reward_tx] + transactions
        new_block = Block(
            index=len(self.chain),
            transactions=all_txs,
            previous_hash=self.get_last_block().hash,
            difficulty=self.difficulty
        )
        new_block.mine()
        return new_block

    def validate_chain(self) -> bool:
        """Verify integrity of the entire chain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if not current.is_valid():
                print(f"[Validation] Block #{i} is invalid")
                return False
            if current.previous_hash != previous.hash:
                print(f"[Validation] Chain broken at block #{i}")
                return False
            if not current.hash.startswith("0" * self.difficulty):
                print(f"[Validation] Block #{i} has insufficient PoW")
                return False
        return True

    def get_balance(self, address: str) -> float:
        """Calculate balance of an address by scanning the chain."""
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if hasattr(tx, 'sender') and tx.sender == address:
                    balance -= tx.amount
                if hasattr(tx, 'receiver') and tx.receiver == address:
                    balance += tx.amount
        return balance

    def to_dict(self) -> dict:
        return {
            "difficulty": self.difficulty,
            "chain": [block.to_dict() for block in self.chain]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Blockchain":
        bc = cls.__new__(cls)
        bc.difficulty = data["difficulty"]
        bc.chain = [Block.from_dict(b) for b in data["chain"]]
        return bc

    def __len__(self):
        return len(self.chain)

    def __repr__(self):
        return f"Blockchain(length={len(self.chain)}, difficulty={self.difficulty})"