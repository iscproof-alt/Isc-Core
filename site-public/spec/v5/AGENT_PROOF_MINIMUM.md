# ISCProof Agent Proof — Minimum Normative Fields
Version: 1.0
Status: FROZEN
Date: 2026-03-24

Every agent proof MUST contain these fields.
Missing any MUST field → non-conformant.

## Minimum Required Fields

### 1. agent_identity (MUST)
{
  "id": "urn:iscproof:agent:<uuid>",
  "did": "did:key:z6Mk...",
  "name": "string",
  "version": "string"
}

### 2. decision (MUST if action_type includes decision)
{
  "query": "string",
  "input_context": {
    "inline": {}
  },
  "reasoning_summary": "string",  // max 1000 chars
  "outcome": "string"
}

### 3. action (MUST if action_type includes action)
{
  "type": "string",
  "target": "string",
  "result": "success | failed | skipped",
  "executed_at": "ISO8601"
}

### 4. input_seals (OPTIONAL but SHOULD)
["urn:iscproof:seal:uuid"]
// Prior seals this decision depends on

### 5. output_hash (MUST if action produced output)
{
  "alg": "sha-256",
  "digest": "hex"
}
// Hash of the action output

### 6. timestamp (MUST)
"ISO8601"
// Agent proof creation time, UTC

### 7. signatures (MUST)
[{
  "signer_id": "did:key:z6Mk...",
  "alg": "Ed25519",
  "value": "base64url",
  "signed_at": "ISO8601"
}]

## Hard Rules

- agent_identity.did MUST be did:key (offline verifiable)
- input_context MUST be inline (no external references)
- reasoning_summary MUST NOT exceed 1000 characters
- output_hash MUST be present if action produced any output
- timestamp MUST be UTC
- Every agent proof MUST be sealed with ISCProof core

## Non-Conformant Cases

- Missing agent_identity → FAIL
- Missing decision when action_type=decision → FAIL
- External input_context reference → FAIL
- Missing output_hash when output exists → FAIL
- reasoning_summary > 1000 chars → FAIL
- Non did:key agent identity → WARN

## Summary

Agent proof answers:
WHO   → agent_identity
WHY   → decision.input_context + reasoning_summary
WHAT  → action
OUTPUT → output_hash
WHEN  → timestamp
CHAIN → input_seals
PROOF → signatures
