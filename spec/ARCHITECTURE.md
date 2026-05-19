# ISCProof Architecture

## Three-Layer Model

### ISCProof — Protocol & Specification
The open standard for cryptographic sealing of AI outputs. Defines seal format, chain linkage, verification protocol, and evidence pack structure. Any party may implement ISCProof independently.

### BuildSeal — Forensic Audit Layer
The reference implementation of ISCProof. Production-grade infrastructure for sealing AI decisions at generation time. Every output is immutable, independently verifiable, and chain-linked via prev_seal_id.

### NYM — Witness Interface
The live representative operating within BuildSeal. NYM does not remember — it retrieves verified sealed evidence. Every exchange is sealed the moment it is produced. NYM is a cryptographic witness, not an oracle.

## Design Principles

- Seal at generation, not after
- Evidence over memory
- Silence over speculation
- Chain integrity over convenience
- Independent verification without vendor dependency

## Positioning

ISCProof is the protocol.
BuildSeal is the forensic audit layer.
NYM is the witness interface.

Each layer is independently verifiable. Each seal is permanently addressable.
