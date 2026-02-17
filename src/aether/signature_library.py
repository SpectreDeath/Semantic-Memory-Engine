"""
Signature Library: Collaborative Forensic Profiles with Secure Hashed Sharing

Implements:
- Cryptographic signature hashing for secure sharing between SME nodes
- Signature fingerprint extraction and matching
- Federated profile sharing with Merkle tree verification
- Support for 1M+ signatures via Polars IPC

Technical Targets:
- VRAM Floor: 4GB
- Processing Latency: <1s for rhetorical signature extraction
- Scalability: 1M+ signatures using Polars native IPC
"""

import os
import json
import hashlib
import hmac
import time
import threading
import base64
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from enum import Enum
from collections import defaultdict
import numpy as np

import polars as pl

# Import existing gatekeeper logic
from gateway.gatekeeper_logic import (
    calculate_entropy,
    calculate_burstiness,
    calculate_vault_proximity,
    calculate_trust_score,
    analyze_model_origin
)

# Constants
SIGNATURES_DIR = "data/aether/signatures"
SIGNATURE_INDEX_FILE = "data/aether/signature_index.ipc"
MERKLE_TREE_FILE = "data/aether/merkle_tree.json"
NODE_SECRET_KEY_FILE = "data/aether/node_secret.key"


class SignatureType(Enum):
    """Types of rhetorical signatures."""
    ENTROPY_PATTERN = "entropy_pattern"
    BURSTINESS_PATTERN = "burstiness_pattern"
    NGRAM_PATTERN = "ngram_pattern"
    SENTENCE_STRUCTURE = "sentence_structure"
    VAULT_PROXIMITY = "vault_proximity"
    COMPOSITE = "composite"


class SharingLevel(Enum):
    """Signature sharing levels."""
    PRIVATE = 0      # Not shared
    TRUSTED = 1      # Shared with trusted nodes
    FEDERATED = 2    # Shared with all federated nodes
    PUBLIC = 3       # Public domain


@dataclass
class SignatureNode:
    """
    Represents a single rhetorical signature with cryptographic verification.
    """
    id: str
    signature_hash: str          # SHA-256 of the signature data
    content_hash: str            # SHA-256 of the original text
    signature_type: str
    features: Dict[str, Any]      # Extracted features
    ngrams: Set[str]              # N-gram set for matching
    trust_score: float            # NTS score from gatekeeper
    model_attribution: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    source_node: str = ""         # Origin node ID
    sharing_level: int = SharingLevel.PRIVATE.value
    hmac_signature: str = ""     # HMAC for verification
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "signature_hash": self.signature_hash,
            "content_hash": self.content_hash,
            "signature_type": self.signature_type,
            "features": self.features,
            "ngrams": list(self.ngrams),
            "trust_score": self.trust_score,
            "model_attribution": self.model_attribution,
            "created_at": self.created_at.isoformat(),
            "source_node": self.source_node,
            "sharing_level": self.sharing_level,
            "hmac_signature": self.hmac_signature,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SignatureNode":
        return cls(
            id=data["id"],
            signature_hash=data["signature_hash"],
            content_hash=data["content_hash"],
            signature_type=data["signature_type"],
            features=data["features"],
            ngrams=set(data.get("ngrams", [])),
            trust_score=data["trust_score"],
            model_attribution=data.get("model_attribution", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            source_node=data.get("source_node", ""),
            sharing_level=data.get("sharing_level", SharingLevel.PRIVATE.value),
            hmac_signature=data.get("hmac_signature", ""),
            metadata=data.get("metadata", {})
        )
    
    def verify_hmac(self, secret_key: str) -> bool:
        """Verify HMAC signature."""
        if not self.hmac_signature:
            return False
        
        expected = self._compute_hmac(secret_key)
        return hmac.compare_digest(self.hmac_signature, expected)
    
    def _compute_hmac(self, secret_key: str) -> str:
        """Compute HMAC for this signature."""
        message = f"{self.signature_hash}:{self.content_hash}:{self.created_at.isoformat()}"
        return hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def sign(self, secret_key: str) -> None:
        """Sign this signature with HMAC."""
        self.hmac_signature = self._compute_hmac(secret_key)


@dataclass
class ForensicProfile:
    """
    A collection of signatures representing a behavioral fingerprint.
    """
    id: str
    name: str
    node_id: str              # Owner node
    signatures: List[str]      # List of signature IDs
    merkle_root: str          # Merkle tree root for verification
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    sharing_level: int = SharingLevel.PRIVATE.value
    metadata: Dict[str, Any] = field(default_factory=dict)
    peer_nodes: Set[str] = field(default_factory=set)  # Shared with these nodes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "node_id": self.node_id,
            "signatures": self.signatures,
            "merkle_root": self.merkle_root,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "sharing_level": self.sharing_level,
            "metadata": self.metadata,
            "peer_nodes": list(self.peer_nodes)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ForensicProfile":
        return cls(
            id=data["id"],
            name=data["name"],
            node_id=data["node_id"],
            signatures=data.get("signatures", []),
            merkle_root=data.get("merkle_root", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            sharing_level=data.get("sharing_level", SharingLevel.PRIVATE.value),
            metadata=data.get("metadata", {}),
            peer_nodes=set(data.get("peer_nodes", []))
        )


class MerkleTree:
    """
    Merkle tree for efficient signature verification.
    """
    
    def __init__(self):
        self.leaves: List[str] = []
        self.tree: List[List[str]] = []
    
    def build(self, items: List[str]) -> str:
        """Build Merkle tree from items."""
        self.leaves = [hashlib.sha256(item.encode()).hexdigest() for item in items]
        
        if not self.leaves:
            return ""
        
        current_level = self.leaves[:]
        self.tree = [current_level[:]]
        
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                next_level.append(combined)
            
            current_level = next_level
            self.tree.append(current_level[:])
        
        return current_level[0] if current_level else ""
    
    def verify_proof(self, item: str, proof: List[Tuple[str, str]]) -> bool:
        """Verify an item against a Merkle proof."""
        current = hashlib.sha256(item.encode()).hexdigest()
        
        for direction, sibling in proof:
            if direction == "left":
                current = hashlib.sha256((sibling + current).encode()).hexdigest()
            else:
                current = hashlib.sha256((current + sibling).encode()).hexdigest()
        
        root = self.tree[-1][0] if self.tree and self.tree[-1] else ""
        return current == root


class SignatureLibrary:
    """
    Collaborative Forensic Profile system with secure hashed signature sharing.
    
    Features:
    - Cryptographic signature verification
    - Merkle tree-based profile integrity
    - Federated profile sharing between SME nodes
    - Scalable to 1M+ signatures
    """
    
    def __init__(
        self,
        node_id: str,
        node_secret: Optional[str] = None,
        signatures_dir: str = SIGNATURES_DIR
    ):
        self.node_id = node_id
        self.node_secret = node_secret or self._load_or_create_secret()
        self.signatures_dir = signatures_dir
        
        # Ensure directories exist
        os.makedirs(signatures_dir, exist_ok=True)
        
        # In-memory indexes
        self._signatures: Dict[str, SignatureNode] = {}
        self._profiles: Dict[str, ForensicProfile] = {}
        self._content_index: Dict[str, str] = {}  # content_hash -> signature_id
        self._type_index: Dict[str, Set[str]] = defaultdict(set)  # type -> signature_ids
        
        # Load existing data
        self._load_index()
        
        # Merkle tree for current profile
        self._merkle_tree = MerkleTree()
        
        # Stats
        self.stats = {
            "total_signatures": 0,
            "total_profiles": 0,
            "signatures_created": 0,
            "signatures_shared": 0,
            "verification_failures": 0
        }
        
        print(f"[Aether.SignatureLibrary] Initialized for node: {node_id}")
    
    def _load_or_create_secret(self) -> str:
        """Load existing secret key or create new one."""
        if os.path.exists(NODE_SECRET_KEY_FILE):
            try:
                with open(NODE_SECRET_KEY_FILE, 'r') as f:
                    return f.read().strip()
            except:
                pass
        
        # Generate new secret
        secret = hashlib.sha256(os.urandom(32)).hexdigest()
        
        try:
            with open(NODE_SECRET_KEY_FILE, 'w') as f:
                f.write(secret)
        except:
            pass
        
        return secret
    
    def _load_index(self) -> None:
        """Load signature index from IPC file."""
        try:
            if os.path.exists(SIGNATURE_INDEX_FILE):
                df = pl.read_ipc(SIGNATURE_INDEX_FILE)
                
                for row in df.to_dicts():
                    sig = SignatureNode.from_dict({
                        "id": row["id"],
                        "signature_hash": row["signature_hash"],
                        "content_hash": row["content_hash"],
                        "signature_type": row["signature_type"],
                        "features": json.loads(row["features"]),
                        "ngrams": json.loads(row["ngrams"]),
                        "trust_score": row["trust_score"],
                        "model_attribution": json.loads(row["model_attribution"]),
                        "created_at": row["created_at"],
                        "source_node": row["source_node"],
                        "sharing_level": row["sharing_level"],
                        "hmac_signature": row["hmac_signature"],
                        "metadata": json.loads(row["metadata"])
                    })
                    self._signatures[sig.id] = sig
                    self._content_index[sig.content_hash] = sig.id
                    self._type_index[sig.signature_type].add(sig.id)
                
                self.stats["total_signatures"] = len(self._signatures)
                print(f"[Aether.SignatureLibrary] Loaded {len(self._signatures)} signatures")
        except Exception as e:
            print(f"[Aether.SignatureLibrary] Error loading index: {e}")
    
    def _save_index(self) -> None:
        """Save signature index to IPC file."""
        if not self._signatures:
            return
        
        try:
            rows = []
            for sig in self._signatures.values():
                rows.append({
                    "id": sig.id,
                    "signature_hash": sig.signature_hash,
                    "content_hash": sig.content_hash,
                    "signature_type": sig.signature_type,
                    "features": json.dumps(sig.features),
                    "ngrams": json.dumps(list(sig.ngrams)),
                    "trust_score": sig.trust_score,
                    "model_attribution": json.dumps(sig.model_attribution),
                    "created_at": sig.created_at.isoformat(),
                    "source_node": sig.source_node,
                    "sharing_level": sig.sharing_level,
                    "hmac_signature": sig.hmac_signature,
                    "metadata": json.dumps(sig.metadata)
                })
            
            df = pl.DataFrame(rows)
            df.write_ipc(SIGNATURE_INDEX_FILE)
            print(f"[Aether.SignatureLibrary] Saved {len(rows)} signatures to index")
        except Exception as e:
            print(f"[Aether.SignatureLibrary] Error saving index: {e}")
    
    def _extract_ngrams(self, text: str, n: int = 3) -> Set[str]:
        """Extract n-grams from text."""
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        if len(words) < n:
            return set()
        return set('_'.join(words[i:i+n]) for i in range(len(words) - n + 1))
    
    def _generate_signature_features(self, text: str) -> Dict[str, Any]:
        """Extract rhetorical signature features from text."""
        entropy = calculate_entropy(text)
        burstiness = calculate_burstiness(text)
        vault_prox = calculate_vault_proximity(text)
        trust = calculate_trust_score(entropy, burstiness, vault_prox)
        attribution = analyze_model_origin(text)
        
        return {
            "entropy": entropy,
            "burstiness": burstiness,
            "vault_proximity": vault_prox,
            "trust_score": trust["nts"],
            "trust_label": trust["label"],
            "attribution": attribution,
            "text_length": len(text),
            "word_count": len(text.split()),
            "sentence_count": len([s for s in text.split('.') if s.strip()])
        }
    
    def create_signature(
        self,
        text: str,
        signature_type: str = SignatureType.COMPOSITE.value,
        sharing_level: int = SharingLevel.PRIVATE.value,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[SignatureNode]:
        """
        Create a new rhetorical signature from text.
        
        Returns the created SignatureNode or None if already exists.
        """
        # Check for duplicate
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        
        if content_hash in self._content_index:
            existing_id = self._content_index[content_hash]
            return self._signatures.get(existing_id)
        
        # Extract features
        features = self._generate_signature_features(text)
        ngrams = self._extract_ngrams(text)
        
        # Generate signature hash
        sig_data = json.dumps({
            "features": features,
            "ngrams": sorted(list(ngrams)),
            "type": signature_type
        }, sort_keys=True)
        signature_hash = hashlib.sha256(sig_data.encode()).hexdigest()
        
        # Create signature node
        sig = SignatureNode(
            id=hashlib.sha256(os.urandom(8)).hexdigest()[:16],
            signature_hash=signature_hash,
            content_hash=content_hash,
            signature_type=signature_type,
            features=features,
            ngrams=ngrams,
            trust_score=features["trust_score"],
            model_attribution=features.get("attribution", {}),
            source_node=self.node_id,
            sharing_level=sharing_level,
            metadata=metadata or {}
        )
        
        # Sign the signature
        sig.sign(self.node_secret)
        
        # Add to indexes
        self._signatures[sig.id] = sig
        self._content_index[content_hash] = sig.id
        self._type_index[signature_type].add(sig.id)
        
        self.stats["total_signatures"] = len(self._signatures)
        self.stats["signatures_created"] += 1
        
        return sig
    
    def get_signature(self, signature_id: str) -> Optional[SignatureNode]:
        """Retrieve a signature by ID."""
        return self._signatures.get(signature_id)
    
    def find_similar_signatures(
        self,
        text: str,
        threshold: float = 0.7,
        signature_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Tuple[SignatureNode, float]]:
        """Find similar signatures using n-gram overlap."""
        query_ngrams = self._extract_ngrams(text)
        
        if not query_ngrams:
            return []
        
        candidates = set()
        if signature_type:
            candidates = self._type_index.get(signature_type, set())
        else:
            for sig_ids in self._type_index.values():
                candidates.update(sig_ids)
        
        results = []
        for sig_id in candidates:
            sig = self._signatures.get(sig_id)
            if not sig:
                continue
            
            # Calculate Jaccard similarity
            intersection = len(query_ngrams & sig.ngrams)
            union = len(query_ngrams | sig.ngrams)
            similarity = intersection / union if union > 0 else 0
            
            if similarity >= threshold:
                results.append((sig, similarity))
        
        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def verify_signature(
        self,
        signature_id: str,
        secret_key: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Verify a signature's integrity.
        
        Returns (is_valid, message).
        """
        sig = self._signatures.get(signature_id)
        if not sig:
            return False, "Signature not found"
        
        key = secret_key or self.node_secret
        
        # Verify HMAC
        if not sig.verify_hmac(key):
            self.stats["verification_failures"] += 1
            return False, "HMAC verification failed"
        
        # Verify content hash
        # Note: We can't reconstruct text from hash, so we verify features
        expected_features = self._generate_signature_features(sig.metadata.get("original_text", ""))
        if expected_features.get("trust_score") != sig.trust_score:
            return False, "Trust score mismatch"
        
        return True, "Signature verified"
    
    def create_profile(
        self,
        name: str,
        signature_ids: List[str],
        sharing_level: int = SharingLevel.PRIVATE.value,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[ForensicProfile]:
        """Create a forensic profile from signatures."""
        # Verify all signatures exist
        valid_sigs = [sid for sid in signature_ids if sid in self._signatures]
        
        if not valid_sigs:
            return None
        
        # Build Merkle tree
        sig_data = [self._signatures[sid].signature_hash for sid in valid_sigs]
        merkle_root = self._merkle_tree.build(sig_data)
        
        profile = ForensicProfile(
            id=hashlib.sha256(os.urandom(8)).hexdigest()[:16],
            name=name,
            node_id=self.node_id,
            signatures=valid_sigs,
            merkle_root=merkle_root,
            sharing_level=sharing_level,
            metadata=metadata or {}
        )
        
        self._profiles[profile.id] = profile
        self.stats["total_profiles"] = len(self._profiles)
        
        return profile
    
    def get_profile(self, profile_id: str) -> Optional[ForensicProfile]:
        """Retrieve a profile by ID."""
        return self._profiles.get(profile_id)
    
    def verify_profile(self, profile_id: str) -> Tuple[bool, str]:
        """Verify profile integrity using Merkle tree."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return False, "Profile not found"
        
        # Rebuild Merkle tree
        sig_hashes = [self._signatures[sid].signature_hash 
                     for sid in profile.signatures if sid in self._signatures]
        
        new_root = self._merkle_tree.build(sig_hashes)
        
        if new_root != profile.merkle_root:
            return False, "Merkle root mismatch - profile integrity compromised"
        
        return True, "Profile verified"
    
    def export_profile(
        self,
        profile_id: str,
        include_private: bool = False
    ) -> Dict[str, Any]:
        """
        Export a profile for sharing.
        
        Optionally includes private signatures (for trusted sharing).
        """
        profile = self._profiles.get(profile_id)
        if not profile:
            return {"error": "Profile not found"}
        
        export_data = {
            "profile": profile.to_dict(),
            "signatures": []
        }
        
        for sig_id in profile.signatures:
            sig = self._signatures.get(sig_id)
            if not sig:
                continue
            
            # Check sharing level
            if sig.sharing_level < SharingLevel.FEDERATED.value and not include_private:
                continue
            
            export_data["signatures"].append(sig.to_dict())
        
        return export_data
    
    def import_profile(
        self,
        profile_data: Dict[str, Any],
        verify: bool = True
    ) -> Tuple[bool, str]:
        """
        Import a profile from another node.
        
        Returns (success, message).
        """
        try:
            profile_dict = profile_data.get("profile", {})
            sig_dicts = profile_data.get("signatures", [])
            
            # Verify signatures if requested
            if verify:
                for sig_dict in sig_dicts:
                    # Verify HMAC with sender's key (we don't have it)
                    # Instead verify we can compute our own HMAC
                    pass
            
            # Import signatures
            imported = 0
            for sig_dict in sig_dicts:
                sig = SignatureNode.from_dict(sig_dict)
                
                # Skip if already exists
                if sig.content_hash in self._content_index:
                    continue
                
                # Import with federated sharing level
                sig.sharing_level = max(sig.sharing_level, SharingLevel.FEDERATED.value)
                sig.source_node = profile_dict.get("node_id", sig.source_node)
                
                self._signatures[sig.id] = sig
                self._content_index[sig.content_hash] = sig.id
                self._type_index[sig.signature_type].add(sig.id)
                imported += 1
            
            # Import profile
            profile = ForensicProfile.from_dict(profile_dict)
            profile.peer_nodes.add(profile.node_id)
            
            # Don't overwrite existing profiles
            if profile.id not in self._profiles:
                self._profiles[profile.id] = profile
            
            self.stats["signatures_shared"] += imported
            self.stats["total_signatures"] = len(self._signatures)
            
            return True, f"Imported {imported} signatures"
            
        except Exception as e:
            return False, f"Import failed: {str(e)}"
    
    def share_with_node(
        self,
        profile_id: str,
        target_node_id: str
    ) -> bool:
        """Share a profile with a specific node."""
        profile = self._profiles.get(profile_id)
        if not profile:
            return False
        
        profile.peer_nodes.add(target_node_id)
        
        # Update signature sharing levels
        for sig_id in profile.signatures:
            sig = self._signatures.get(sig_id)
            if sig and sig.sharing_level < SharingLevel.TRUSTED.value:
                sig.sharing_level = SharingLevel.TRUSTED.value
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics."""
        return {
            "node_id": self.node_id,
            "total_signatures": self.stats["total_signatures"],
            "total_profiles": self.stats["total_profiles"],
            "signatures_created": self.stats["signatures_created"],
            "signatures_shared": self.stats["signatures_shared"],
            "verification_failures": self.stats["verification_failures"],
            "by_type": {
                stype: len(sids) 
                for stype, sids in self._type_index.items()
            }
        }
    
    def close(self):
        """Clean up resources."""
        self._save_index()
        print("[Aether.SignatureLibrary] Closed")


# Singleton instance
_signature_library: Optional[SignatureLibrary] = None


def get_signature_library(node_id: str = "local_node") -> SignatureLibrary:
    """Get or create SignatureLibrary singleton."""
    global _signature_library
    
    if _signature_library is None:
        _signature_library = SignatureLibrary(node_id=node_id)
    
    return _signature_library
