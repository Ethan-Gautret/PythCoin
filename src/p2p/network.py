import requests
import json
from .peer import Peer


class P2PNetwork:
    """Manages peer discovery and message broadcasting."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5000):
        self.host = host
        self.port = port
        self.peers: list[Peer] = []
        self._seen_messages: set = set()  # Anti-loop: track seen message IDs

    def add_peer(self, peer: Peer) -> bool:
        """Add a peer if not already known."""
        if peer not in self.peers and not (peer.address == self.host and peer.port == self.port):
            self.peers.append(peer)
            print(f"[P2P] Peer added: {peer}")
            return True
        return False

    def remove_peer(self, peer: Peer) -> None:
        if peer in self.peers:
            self.peers.remove(peer)

    def broadcast(self, endpoint: str, data: dict, message_id: str = None) -> None:
        """Broadcast data to all known peers."""
        if message_id:
            if message_id in self._seen_messages:
                return  # Anti-loop: already seen
            self._seen_messages.add(message_id)

        for peer in list(self.peers):
            try:
                url = f"{peer.url}/{endpoint}"
                requests.post(url, json=data, timeout=3)
                print(f"[P2P] Broadcast to {peer}: /{endpoint}")
            except requests.exceptions.RequestException as e:
                print(f"[P2P] Failed to reach {peer}: {e}")
                self.remove_peer(peer)

    def broadcast_transaction(self, tx_dict: dict) -> None:
        self.broadcast("transactions/receive", tx_dict, message_id=tx_dict.get("id"))

    def broadcast_block(self, block_dict: dict) -> None:
        block_id = f"block-{block_dict.get('index')}-{block_dict.get('hash', '')[:8]}"
        self.broadcast("blocks/receive", block_dict, message_id=block_id)

    def discover_peers(self, bootstrap_peer: Peer) -> None:
        """Ask a known peer for its peer list."""
        try:
            response = requests.get(f"{bootstrap_peer.url}/peers", timeout=3)
            peers_data = response.json().get("peers", [])
            for p in peers_data:
                self.add_peer(Peer.from_dict(p))
        except Exception as e:
            print(f"[P2P] Discovery failed from {bootstrap_peer}: {e}")

    def get_longest_chain(self) -> dict | None:
        best_chain = None
        best_length = 0
        for peer in self.peers:
            try:
                response = requests.get(f"{peer.url}/chain", timeout=5)
                print(f"[P2P] Chain from {peer}: status {response.status_code}")
                chain_data = response.json()
                print(f"[P2P] Chain length from {peer}: {chain_data.get('length', 0)}")
                length = chain_data.get("length", 0)
                if length > best_length:
                    best_length = length
                    best_chain = chain_data
            except Exception as e:
                print(f"[P2P] Error fetching chain from {peer}: {e}")
        return best_chain

    def to_dict(self) -> dict:
        return {"peers": [p.to_dict() for p in self.peers]}

    def __repr__(self):
        return f"P2PNetwork({self.host}:{self.port}, peers={len(self.peers)})"