# Seal v3 (ISC_SEAL_V3_VEDM)

## Status
Experimental. Extends ISC_SEAL_V2 with epistemic state binding.

## Motivation

ISC_SEAL_V2 binds a decision to its output and registry state.
It does not bind the epistemic state from which the decision emerged.

Without epistemic binding:
  P(decision_t) = f(input_t, weights)

With epistemic binding:
  P(decision_t) = f(input_t, weights, H(seal_chain_{0→t-1}))

Reproducibility requires sealed epistemic trajectory.
Epistemic state becomes part of the signed computational boundary.

## Core Principle

ISC_SEAL_V3 enables replay not only of decisions, but of the
epistemic conditions under which those decisions emerged.

  v2 = output integrity
  v3 = output integrity + epistemic integrity

## New Signing Input

  ISC_SEAL_V3\0 || PACK_SHA256_BYTES || REGISTRY_ID_FIELD
                || REG_SNAPSHOT_SHA256_BYTES || EPISTEMIC_STATE_FIELD

## EPISTEMIC_STATE_FIELD

  EPISTEMIC_STATE_FIELD = U32BE(len(EPISTEMIC_STATE_BYTES)) || EPISTEMIC_STATE_BYTES

Where EPISTEMIC_STATE_BYTES is SHA-256 of canonical JSON:

{
  "epistemic_delta": "<canonical description of epistemic state transition between t-1 and t>",
  "H_cumulative": "<SHA256 of full epistemic chain commitment up to this seal>",
  "decay_policy_id": "<policy identifier>",
  "decay_policy_hash": "<SHA256(policy definition canonical bytes)>",
  "epistemic_distribution": {
    "recent_weight": 0.62,
    "compressed_weight": 0.28,
    "archived_weight": 0.10
  }
}

## Epistemic Delta (ΔH_t)

ΔH_t is NOT hash subtraction (undefined in hash space).

ΔH_t := canonicalized description of epistemic state transition
         between seal_{t-1} and seal_t.

Contents:
  - sealed decisions since previous seal
  - contradiction events and affected seal_ids
  - resurrection events (archived → resurrected tier)
  - decay policy changes
  - memory tier transitions

## H_cumulative

H_cumulative is the epistemic chain commitment:
  SHA256(canonical(seal_chain_{0→t}))

This means:
  decision integrity now depends on epistemic lineage integrity.

## decay_policy_hash

Policy identifier alone is insufficient — identifier may later point
to a different policy definition.

decay_policy_hash = SHA256(canonical policy definition bytes)

Forensic verifier MUST check policy definition matches hash,
not only identifier.

## epistemic_distribution

Captures influence weighting at decision time:
  recent_weight + compressed_weight + archived_weight = 1.0

Required for forensic replay to reconstruct epistemic influence
distribution, not only tier counts.

## Legacy Compatibility

ISC_SEAL_V2 seals:
  "epistemic_guarantee": false

ISC_SEAL_V3 seals:
  "epistemic_guarantee": true
  "vedm_version": "0.1"

## Forensic Replay Procedure

1. Collect all seals in chain ordered by sequence_num
2. For each seal_t: verify epistemic_delta is consistent with
   prior H_cumulative
3. Verify decay_policy_hash matches declared policy definition
4. Verify epistemic_distribution sums to 1.0
5. Reconstruct epistemic state at any point t

Output: complete epistemic trajectory from t=0 to t=n.
        "From which epistemic state did this decision emerge?"
        is now cryptographically answerable.

## Attack Model

Epistemic Manipulation Attack:
  Adversary attempts to alter H_cumulative retrospectively.
  Mitigation: H_cumulative is part of signed boundary —
  any alteration invalidates Ed25519 signature.

Decay Policy Substitution Attack:
  Adversary replaces policy definition after sealing.
  Mitigation: decay_policy_hash commits to exact policy bytes.

Epistemic Inflation Attack:
  Adversary spams retrieval to inflate F_r linearly.
  Mitigation: ln(F_r) logarithmic scaling bounds influence growth.

## References

- ISC_SEAL_V2: SEAL_V2.md
- VEDM Specification: VEDM-SPEC-v0.1.md (forthcoming)
- Epistemic Decay Function: E_f(S) = T(S)·[1+α·ln(F_r)]·S_c / e^(λ·Δt)

## Test Vector — Genesis V3 Seal

seal_id:             seal_1779537745159_kimb7ltv
seal_version:        ISC_SEAL_V3
epistemic_guarantee: true
delta_H:             f1e7e616ceb50ad13ed91d5df61220a5e11bf92f5862bde93f18f323a18c40f5
H_cumulative:        fa5238d38fa18a67c976d70079352e049484d44fd0269702de80540dcc45916f
decay_policy:        vedm-0.1
decay_policy_hash:   595b57c068a875193c6614ab5779d2ecdb218009fb817c09254af5fb10ba2157
root:                c40afeb5835798d1238f7cc0daaacde9a3df9dbd1e0183b37e3a32c0c40df4c8
alg:                 ed25519
fingerprint:         a5ec97589519d9ee
sealed_at:           2026-05-23T12:02:25Z
verify_url:          https://buildseal.io/verify?id=seal_1779537745159_kimb7ltv
pack_url:            https://buildseal-api-production-3ca5.up.railway.app/pack/seal_1779537745159_kimb7ltv

## Test Vector 2 — V3 Policy Hash Verified

seal_id:             seal_1779555297219_kglb3ay6
seal_version:        ISC_SEAL_V3
epistemic_guarantee: true
delta_H:             4ba7a1718d89b6940b398faaaf31046e50536e9882ac2499075973363919ca11
H_cumulative:        755fd32b51eebf78d1d76a5aa0fc0be4c9b8e34bc5295d1585b8d0d9cb58d977
decay_policy:        vedm-0.1
decay_policy_hash:   4ca8f54a6c9a4429f58adaa7d4b9ee86876c519785ed442cff04a9e7a9026a8e
policy_hash_check:   VALID
root:                b2233c69a54b166400a89ca0daa8d482992c23609bf9c16e8185813fa63232d8
fingerprint:         a5ec97589519d9ee
sealed_at:           2026-05-23T17:14:57Z
