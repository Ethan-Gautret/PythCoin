class Peer:
    """Represents a remote peer in the P2P network."""

    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port

    @property
    def url(self) -> str:
        return f"http://{self.address}:{self.port}"

    def to_dict(self) -> dict:
        return {"address": self.address, "port": self.port}

    @classmethod
    def from_dict(cls, data: dict) -> "Peer":
        return cls(data["address"], data["port"])

    def __eq__(self, other):
        return self.address == other.address and self.port == other.port

    def __hash__(self):
        return hash((self.address, self.port))

    def __repr__(self):
        return f"Peer({self.address}:{self.port})"