# ISCProof Evidence Pack V4

Status: Draft
Supersedes: Evidence Pack V3 (sealed-record format, now frozen)
Scope: Canonical evidence pack format for ISCProof
Non-goals: CI integration, registry, reproducibility guarantees, PKI, identity management

---

## 1. Status and Intent

V3 proved the model. V4 defines the format.

V3 established that a sealing event could be expressed as a portable, self-contained record. That model is correct. V3 is frozen: no new features, read and verify support only.

V4 changes the identity model. In V3, identity was a signed record. In V4, identity is a pack root hash. This is not a minor version change. It is a different ontology.

New implementations must use V4. V3 remains valid for existing packs.

---

## 2. Design Invariants

These invariants must hold across all versions of V4. Format details may evolve. These must not.

- Pack identity is the root hash.
- The root hash commits to all leaves.
- Leaves are content-addressed.
- Verification must not require network access.
- A pack must be self-contained.
- Unknown non-critical extensions must not break verification.
- Unknown critical extensions must cause verification to fail.
- The root hash is computed over canonical CBOR encoding.
- The signature covers the root hash, not individual leaves.
- Pack identity represents a sealing event, not an artifact.
- Canonical ordering must produce identical root hashes across implementations.

The last sealing invariant is the most important. A pack root does not identify a file. It identifies the event of sealing: this artifact, with this attestation, under this metadata, at this moment, by this key.

---

## 3. Pack Identity Model

Pack identity is derived as follows:

    leaves   = sorted set of typed leaf hashes
    root     = hash(hash_alg, canonical_cbor(leaves))
    pack_id  = root

hash_alg is declared in the pack header (see Section 8).

The pack_id is the canonical identifier for a sealing event. It is stable, portable, and verifiable without external state.

This mirrors the Git commit model: a commit hash identifies a snapshot event, not a file tree. The pack root identifies a sealing event, not an artifact.

---

## 4. Canonical Encoding

All encoding uses deterministic CBOR as defined in RFC 8949 Section 4.2.

Rules:
- No optional field ordering
- No whitespace or padding
- No JSON fallback or dual encoding
- All hashes are computed over canonical CBOR encoding of the relevant structure
- Non-canonical CBOR MUST cause verification failure
- Implementations must reject non-canonical encodings immediately, not silently correct them

---

## 5. Leaf Model

A leaf is a typed content address:

    leaf = (type_tag: uint, leaf_hash: bytes)

leaf_payload is the CBOR structure associated with the leaf. The leaf_hash is computed as:

    leaf_hash = hash(hash_alg, canonical_cbor(leaf_payload))

This binding is mandatory. Each leaf_hash MUST equal hash(hash_alg, canonical_cbor(leaf_payload)) using the hash_alg declared in the pack header. A verifier must recompute and confirm this binding before accepting any leaf.

Type tag ranges:

    0x01-0x3F  core leaves (required and defined by this spec)
    0x40-0x7F  critical extensions (unknown tag in range: fail verification)
    0x80-0xBF  optional extensions (unknown tag in range: ignore)
    0xC0-0xFF  private / experimental (no interoperability guarantee)

Defined core tags:

    0x01  artifact     Required. Hash of the sealed artifact.
    0x02  attestation  Required. Hash of the attestation record.
    0x03  metadata     Required. Hash of pack metadata (tool, platform, timestamps).
    0x04  policy       Optional core leaf. Hash of applicable policy document.

---

## 6. Ordering Rule

Leaves must be sorted before root computation:

    sort by (type_tag ASC, leaf_hash ASC)

This rule is deterministic across implementations. Multiple leaves of the same type are permitted and must be ordered by leaf_hash. Ordering must be identical across all conforming implementations. A verifier must reject a pack whose leaves are not in canonical order.

---

## 7. Root Computation

    root = hash(hash_alg, canonical_cbor([ leaf_1, leaf_2, ..., leaf_n ]))

Where each leaf_i is the tuple (type_tag, leaf_hash), the list is sorted per Section 6, and hash_alg is declared in the pack header.

The root is the canonical identity of the pack. Its byte length depends on hash_alg.

Defined hash_alg values:

    "sha256"     SHA-256, 32 bytes output.
    "sha384"     SHA-384, 48 bytes output.
    "sha512"     SHA-512, 64 bytes output.

Verifiers MUST support "sha256". Verifiers MAY support additional algorithms. Verifiers must reject packs with unknown hash_alg values.

---

## 8. Signature Model

The signature is external to the Merkle tree. It is not a leaf.

A pack MUST contain at least one signature. A verifier MUST require at least one valid signature.

The pack carries a list of signatures to support multi-sign, witness signatures, and future algorithm agility:

    signatures: [
      {
        alg:        string,
        public_key: bytes,
        signature:  bytes
      },
      ...
    ]

Currently defined signature algorithms:

    "ed25519"     Ed25519. Default.
    "ecdsa-p256"  ECDSA over P-256. For FIPS environments.

The full pack structure is:

    {
      version:    4,
      hash_alg:   string,
      root:       bytes,
      leaves:     [ (type_tag, leaf_hash), ... ],
      payloads:   [ (leaf_hash, canonical_cbor_payload), ... ],
      signatures: [ { alg, public_key, signature }, ... ]
    }

Payloads are indexed by leaf_hash, not by type_tag. This supports multiple leaves of the same type without ambiguity. Payload entries may appear in any order. Verification must not depend on payload order.

A verifier must:
1. Check version field is 4 before any other parsing
2. Recompute each leaf_hash from its payload using hash_alg
3. Confirm leaves are in canonical order per Section 6
4. Recompute root from sorted leaves using hash_alg
5. Check recomputed root matches the declared root field
6. Verify at least one signature over the root
7. Resolve key trust independently (see TRUST_MODEL.md)

---

## 9. Partial Disclosure

The leaf model supports partial disclosure. A verifier may confirm a single leaf (for example, the artifact hash) without receiving all payloads.

A verifier MAY receive a subset of payloads, but MUST verify the root and signature before accepting any leaf as valid.

Partial verification is valid only after root hash verification and signature verification succeed. A leaf must not be considered verified unless the root is first confirmed. Presenting a leaf hash without a verified root provides no integrity guarantee.

---

## 10. Extension Rules

Optional extensions (0x80-0xBF range):
- Unknown tag in this range: ignore and continue verification
- Verification must not fail due to unrecognized optional leaves

Critical extensions (0x40-0x7F range):
- Unknown tag in this range: fail verification immediately
- A verifier must not silently skip unknown critical leaves

Private/experimental range (0xC0-0xFF):
- No interoperability guarantee
- Verifiers SHOULD ignore private tags unless local policy forbids them
- Must not be used in production packs intended for third-party verification

This pattern follows TUF and X.509 precedent and ensures forward compatibility for optional features while enforcing strict behavior for security-relevant extensions.

---

---

## 4.x Deterministic Canonical Processing Requirements

This specification requires that pack construction and verification be fully deterministic.

Given the same semantic input, independent implementations MUST produce identical leaf hashes, identical leaf ordering, and identical pack_root values.

Determinism is a normative requirement for all stages of pack processing.

### 4.x.1 Canonical Payload Encoding

Leaf payloads MUST be encoded using a deterministic canonical representation.

Implementations MUST use canonical CBOR encoding as defined in RFC 8949 Section 4.2, unless explicitly specified otherwise by this specification.

Requirements:
- The same semantic payload MUST produce identical byte representation.
- Map keys MUST be sorted according to canonical CBOR rules.
- Floating-point normalization MUST follow canonical CBOR rules.
- No implementation-specific formatting is allowed.
- JSON MUST NOT be used as normative encoding for hashing.
- JSON MAY be used for debugging or display, but MUST NOT be used as input to hash computation.

The byte sequence produced by canonical encoding is the exact input to leaf hashing:

    leaf_hash = HASH(canonical_payload_bytes)

### 4.x.2 Leaf Hash Determinism

Leaf hash computation MUST be deterministic.

For a given canonical payload byte sequence, all implementations MUST produce the same leaf_hash.

The hash function MUST be explicitly defined by the pack header hash_alg field. Implementations MUST NOT change hash algorithms implicitly.

The leaf hash input MUST be exactly the canonical payload bytes, without additional whitespace, formatting, or transport encoding.

### 4.x.3 Deterministic Leaf Ordering

Leaves MUST be sorted before root computation. Sorting MUST be deterministic.

    sort by (type_tag ASC, leaf_hash ASC)

Where:
- type_tag is compared as unsigned integer
- leaf_hash is compared as byte string using lexicographic byte order
- comparison MUST NOT use string, hex, or locale-dependent ordering

All implementations MUST produce identical ordering for the same leaf set.

### 4.x.4 Deterministic Pack Root Computation

The pack root MUST be computed from the canonical ordered leaf set:

    pack_root = HASH(canonical_encoding(sorted_leaves))

The encoding MUST be deterministic and canonical. Implementations MUST use canonical CBOR encoding for the leaf list. The same leaf set MUST produce the same pack_root across all implementations.

### 4.x.5 Pack Serialization Determinism

Pack serialization format MUST NOT affect pack_root.

Hash inputs MUST use canonical encoding. pack_root MUST NOT depend on container format. Verification MUST reconstruct canonical representation before hashing.

Pack formats MAY evolve, but canonical hashing rules MUST remain stable.

### 4.x.6 Independent Implementation Requirement

Given the same semantic input, two independent implementations MUST produce:
- identical canonical payload bytes
- identical leaf_hash values
- identical leaf ordering
- identical pack_root

If this condition does not hold, the implementation is non-conformant.

### 4.x.7 Test Vector Requirement

This specification REQUIRES publication of test vectors.

Each test vector MUST include: input payloads, canonical payload bytes, leaf hashes, sorted leaf list, and pack_root.

Implementations MUST verify correctness against published test vectors. An implementation that fails test vector verification MUST be considered non-conformant.

---

---

## 4.y Canonical Test Vector Format

Test vectors MUST be published alongside this specification. This section defines the required format.

### 4.y.1 Test Vector Structure

Each test vector MUST be a JSON document with the following fields:

    {
      "version":            4,
      "hash_alg":           "sha256",
      "inputs": {
        "artifact_payload":     { ... },
        "attestation_payload":  { ... },
        "metadata_payload":     { ... }
      },
      "canonical_encoding":   string (description of encoding used),
      "canonical_bytes": {
        "0x01_artifact":     string (canonical byte representation),
        "0x02_attestation":  string (canonical byte representation),
        "0x03_metadata":     string (canonical byte representation)
      },
      "leaf_hashes": {
        "0x01_artifact":     string (hex),
        "0x02_attestation":  string (hex),
        "0x03_metadata":     string (hex)
      },
      "sorted_leaves": [
        { "type_tag": uint, "type_tag_hex": string, "leaf_hash": string }
      ],
      "root_input":  string (exact bytes fed to root hash),
      "pack_root":   string (hex, expected result)
    }

### 4.y.2 Conformance Requirement

An implementation MUST be tested against all published test vectors before being considered conformant.

For each test vector, the implementation MUST:
- Reproduce identical canonical_bytes from the given inputs
- Reproduce identical leaf_hashes from canonical_bytes
- Reproduce identical sorted_leaves ordering
- Reproduce identical pack_root from sorted_leaves

Any deviation is a conformance failure.

### 4.y.3 Canonical Encoding Note

Test Vector 001 uses sorted-key JSON with no whitespace as a deterministic baseline:

    canonical_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':'))

This is a temporary baseline. When canonical CBOR encoding is fully specified and reference-implemented, CBOR-based test vectors will supersede JSON-based vectors.

JSON-based test vectors remain valid for implementations that have not yet migrated to CBOR. CBOR-based test vectors will be published as a separate series (vector_cbor_001, etc.).

### 4.y.4 Test Vector Publication

Published test vectors are located at:

    test_vectors/v4/vector_001.json

New test vectors MUST be added for:
- Each new leaf type
- Each new hash algorithm
- Each extension tag
- Each known edge case (odd leaf count, duplicate type_tag, empty optional leaves)

---

## 11. V3 Compatibility

V3 remains valid. V3 packs must continue to verify correctly.

    V3  sealed-record format    frozen, no new features
    V4  pack-root format        canonical, all new development

Verifiers should support both formats. The version field MUST be checked before any parsing of pack contents. New sealing tools must produce V4. New features must not be backported to V3. A verifier must not accept a V4 pack processed under V3 rules or vice versa.

---

## 12. Security Considerations

Hash collision: pack integrity depends on the collision resistance of hash_alg. A collision in leaf_hash or root hash breaks integrity. A collision on the root hash would allow a different leaf set to produce the same pack_id. SHA-256 is currently considered collision-resistant for this purpose. Algorithm agility in Section 7 allows migration if this changes.

Key compromise: a compromised producer key invalidates all packs signed by that key. Key revocation is outside this spec. See TRUST_MODEL.md.

Partial disclosure: safe only after root and signature verification. See Section 9.

Replay: a valid pack from time T remains verifiable at time T+N. ISCProof does not prevent replay. Replay resistance requires an external time anchor such as RFC 3161. This is outside the pack format scope.

Downgrade: a verifier that accepts both V3 and V4 must not allow a V4 pack to be processed under V3 rules. The version field is mandatory and must be checked before dispatch.

Non-canonical encoding: a verifier must reject non-canonical CBOR immediately. Silent correction of encoding errors must not occur, as it would allow multiple byte sequences to produce the same root hash.

---

## 13. Non-Goals

The following are explicitly out of scope for this specification:

- Certificate authority or PKI
- Built-in registry or transparency log
- Reproducibility guarantees
- CI or build system integration
- Identity provider or OIDC integration
- Network transport protocol
- Hosting or distribution mechanism

These may be built on top of ISCProof. They must not be built into it.

---

ISCProof Evidence Pack V4 - Draft
Part of the ISCProof specification. See also: TRUST_MODEL.md, SECURITY_MODEL.md


---

## Future: Trusted Timestamp (RFC 3161)

Planned leaf tag: 0x05 (timestamp)

When added:
- Producer requests TSA signature over pack_root at seal time
- TSA response stored as 0x05 leaf payload
- Verifier can confirm pack existed before a given time
- Offline verification remains possible (TSA response self-contained)

Verification policy (accepted TSA, trust rules) is defined in TRUST_MODEL.md.

This extension does not break V4.
It adds a new optional core leaf.
Tag 0x05 is reserved for this purpose.
