from src.core.transaction import Transaction
from src.core.state import WorldState
from .smart_contract import SmartContract, CounterContract, EscrowContract, ConditionalTransferContract


class ContractEngine:
    """
    Manages smart contract registration and deterministic execution.
    All nodes running the same contracts on the same transactions
    must reach the same final state.
    """

    def __init__(self, world_state: WorldState):
        self.world_state = world_state
        self._contracts: dict[str, SmartContract] = {}

    def deploy_contract(self, contract: SmartContract) -> None:
        """Register a contract in the engine."""
        self._contracts[contract.contract_id] = contract
        self.world_state.set_contract_state(contract.contract_id, contract.get_state())
        print(f"[ContractEngine] Deployed: {contract.contract_id}")

    def run(self, tx: Transaction) -> bool:
        """
        Execute a contract call from a transaction.
        tx.receiver = contract_id
        tx.data = {"action": "...", ...}
        """
        contract_id = tx.receiver
        if contract_id not in self._contracts:
            return False

        contract = self._contracts[contract_id]
        # Restore contract state from world_state (determinism)
        saved_state = self.world_state.get_contract_state(contract_id)
        if saved_state:
            contract.state = saved_state

        result = contract.execute(tx, self.world_state)
        return result

    def get_contract(self, contract_id: str) -> SmartContract | None:
        return self._contracts.get(contract_id)

    def create_counter(self, contract_id: str, owner: str) -> CounterContract:
        c = CounterContract(contract_id, owner)
        self.deploy_contract(c)
        return c

    def create_escrow(self, contract_id: str, owner: str,
                      buyer: str, seller: str, amount: float) -> EscrowContract:
        c = EscrowContract(contract_id, owner, buyer, seller, amount)
        self.deploy_contract(c)
        return c

    def create_conditional_transfer(self, contract_id: str, owner: str,
                                    sender: str, receiver: str,
                                    amount: float, required_approvals: int = 2) -> ConditionalTransferContract:
        c = ConditionalTransferContract(contract_id, owner, sender, receiver, amount, required_approvals)
        self.deploy_contract(c)
        return c

    def __repr__(self):
        return f"ContractEngine(contracts={list(self._contracts.keys())})"