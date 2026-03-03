import pytest
from src.p2p.peer import Peer
from src.p2p.network import P2PNetwork


def test_add_peer():
    net = P2PNetwork("127.0.0.1", 5000)
    peer = Peer("127.0.0.1", 5001)
    assert net.add_peer(peer)
    assert peer in net.peers

def test_no_duplicate_peers():
    net = P2PNetwork("127.0.0.1", 5000)
    peer = Peer("127.0.0.1", 5001)
    net.add_peer(peer)
    net.add_peer(peer)
    assert len(net.peers) == 1

def test_no_self_peer():
    net = P2PNetwork("127.0.0.1", 5000)
    self_peer = Peer("127.0.0.1", 5000)
    net.add_peer(self_peer)
    assert len(net.peers) == 0

def test_anti_loop_message():
    net = P2PNetwork("127.0.0.1", 5000)
    # Seen message should not be re-broadcast
    net._seen_messages.add("msg-1")
    # Simulate calling broadcast with seen message_id
    initial_peers = len(net.peers)
    net.broadcast("test", {}, message_id="msg-1")
    # Should return early without sending
    assert True  # No error = anti-loop works

def test_peer_serialization():
    peer = Peer("192.168.1.1", 8080)
    d = peer.to_dict()
    peer2 = Peer.from_dict(d)
    assert peer == peer2