# ISCProof Agent Decision Model
Version: 1.0
Status: FROZEN
Date: 2026-03-22

An agent MUST seal the reason for an action, not just the action itself.

## Decision Record Format

{
  "agent": "iscproof/agent/<name>@<version>",
  "observation": {},
  "rule": "string",
  "decision": {
    "severity": "info | warn | alert",
    "confidence": 0.0-1.0
  },
  "action": {
    "type": "string",
    "target": "string"
  },
  "reason": "string"
}

## Rules

- observation MUST be present
- rule MUST be named
- decision.severity MUST be one of: info, warn, alert
- reason MUST be human-readable
- Every decision record MUST be sealed with ISCProof
