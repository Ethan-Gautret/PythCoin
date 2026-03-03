from src.core.transaction import Transaction


class SmartContract:
    """Base class for smart contracts with deterministic execution."""

    def __init__(self, contract_id: str, owner: str):
        self.contract_id = contract_id
        self.owner = owner
        self.state: dict = {}

    def execute(self, tx: Transaction, world_state) -> bool:
        """Execute contract logic. Override in subclasses."""
        raise NotImplementedError

    def get_state(self) -> dict:
        return self.state.copy()

    def __repr__(self):
        return f"SmartContract(id={self.contract_id}, owner={self.owner[:12]}...)"


# ---- Concrete contracts ----

class CounterContract(SmartContract):
    """Simple counter contract: anyone can increment."""

    def __init__(self, contract_id: str, owner: str):
        super().__init__(contract_id, owner)
        self.state = {"count": 0}

    def execute(self, tx: Transaction, world_state) -> bool:
        action = tx.data.get("action")
        if action == "increment":
            self.state["count"] += 1
            world_state.set_contract_state(self.contract_id, self.state)
            print(f"[Contract] Counter incremented to {self.state['count']}")
            return True
        if action == "reset" and tx.sender == self.owner:
            self.state["count"] = 0
            world_state.set_contract_state(self.contract_id, self.state)
            print(f"[Contract] Counter reset by owner")
            return True
        return False


class EscrowContract(SmartContract):
    """
    Escrow contract:
    - Buyer locks funds (deposit)
    - Seller confirms delivery (release) → funds go to seller
    - Buyer can cancel before release → refund
    """

    def __init__(self, contract_id: str, owner: str, buyer: str,
                 seller: str, amount: float):
        super().__init__(contract_id, owner)
        self.state = {
            "buyer": buyer,
            "seller": seller,
            "amount": amount,
            "status": "pending",   # pending → funded → released / cancelled
            "funded": False,
        }

    def execute(self, tx: Transaction, world_state) -> bool:
        action = tx.data.get("action")
        state = self.state

        if action == "fund" and tx.sender == state["buyer"]:
            if state["status"] != "pending":
                return False
            buyer_balance = world_state.get_balance(state["buyer"])
            if buyer_balance < state["amount"]:
                print("[Escrow] Insufficient buyer balance")
                return False
            world_state.update_balance(state["buyer"], -state["amount"])
            state["status"] = "funded"
            state["funded"] = True
            world_state.set_contract_state(self.contract_id, state)
            print(f"[Escrow] Funded by buyer: {state['amount']}")
            return True

        if action == "release" and tx.sender == state["seller"]:
            if state["status"] != "funded":
                return False
            world_state.update_balance(state["seller"], state["amount"])
            state["status"] = "released"
            world_state.set_contract_state(self.contract_id, state)
            print(f"[Escrow] Released to seller: {state['amount']}")
            return True

        if action == "cancel" and tx.sender == state["buyer"]:
            if state["status"] != "funded":
                return False
            world_state.update_balance(state["buyer"], state["amount"])
            state["status"] = "cancelled"
            world_state.set_contract_state(self.contract_id, state)
            print(f"[Escrow] Cancelled, refunded to buyer")
            return True

        return False


class ConditionalTransferContract(SmartContract):
    """
    Transfer funds only if a condition is met
    (e.g., a required approval count is reached).
    """

    def __init__(self, contract_id: str, owner: str,
                 sender: str, receiver: str, amount: float, required_approvals: int = 2):
        super().__init__(contract_id, owner)
        self.state = {
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "approvals": [],
            "required_approvals": required_approvals,
            "executed": False,
        }

    def execute(self, tx: Transaction, world_state) -> bool:
        action = tx.data.get("action")
        state = self.state

        if action == "approve":
            if tx.sender in state["approvals"] or state["executed"]:
                return False
            state["approvals"].append(tx.sender)
            print(f"[ConditionalTransfer] Approval from {tx.sender[:12]}... "
                  f"({len(state['approvals'])}/{state['required_approvals']})")

            if len(state["approvals"]) >= state["required_approvals"]:
                balance = world_state.get_balance(state["sender"])
                if balance < state["amount"]:
                    print("[ConditionalTransfer] Insufficient balance")
                    return False
                world_state.update_balance(state["sender"], -state["amount"])
                world_state.update_balance(state["receiver"], state["amount"])
                state["executed"] = True
                print(f"[ConditionalTransfer] Transfer executed: {state['amount']}")

            world_state.set_contract_state(self.contract_id, state)
            return True

        return False