"""
Extension-facing Nexus API (protocol).

Extensions receive a nexus_api object when registered. To avoid coupling
to gateway internals, extensions should use only the methods/properties
defined by this interface.

Required:
  - nexus: Database access (execute, query). Extensions use nexus_api.nexus.execute/query.
  - get_hsm(): Returns the HardwareSecurity module for evidence signing/verification.

Optional (for richer bridges like SmeCoreBridge):
  - get_session_entry, get_session, register_provenance, etc.

Import this module for type hints only. The gateway constructs and passes
the actual implementation (SmeCoreBridge or DefaultExtensionContext).
"""
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class NexusDB(Protocol):
    """Minimal DB interface: execute (writes) and query (reads)."""
    def execute(self, sql: str, params: tuple = ()) -> Any: ...
    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]: ...


@runtime_checkable
class NexusAPI(Protocol):
    """
    Interface passed to extensions via register_extension(manifest, nexus_api).
    Extensions must not import gateway.hardware_security or gateway.nexus_db;
    use nexus_api.get_hsm() and nexus_api.nexus instead.
    """
    @property
    def nexus(self) -> NexusDB: ...

    def get_hsm(self) -> Any:
        """Return the HardwareSecurity module (TPM/HSM) for signing/verification."""
        ...
