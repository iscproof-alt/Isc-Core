# ISCProof Trust Foundation
Version: 1.0
Status: FROZEN
Date: 2026-03-22

These three rules are the trust foundation of ISCProof.
No version, profile, or implementation may violate these rules.

## Rule 1: Independent Timestamp

Timestamp MUST be produced by independent RFC 3161 TSA.
BuildSeal MUST NOT issue timestamps from own infrastructure.

## Rule 2: Offline Verification

Evidence pack MUST be offline-verifiable without BuildSeal API.
Verify tool MUST NOT require network access for core verification.

## Rule 3: Client-Side Key

Private key MUST be generated client-side.
Private key MUST NOT be transmitted to or stored by BuildSeal servers.

## Summary

Independent timestamp -> time proof from third party
Offline verify -> no service dependency
Client-side key -> user owns the signature

"The proof is yours. You don't need us."

---

## Trust Levels

### Level 1 — Cryptographic (current)
Signature + RFC 3161 timestamp + offline verify.
Sufficient for production use.
Industry standard model.

### Level 2 — Witnessed (future)
Level 1 + multiple independent witnesses.
Distributed log + Merkle anchor.

### Level 3 — Consensus (TrustNet)
Level 2 + consensus network.
Independent nodes + append-only history.
No central authority.

TrustNet is Level 3.
Current system is Level 1.
Architecture supports Level 2 and 3 without breaking Level 1.
