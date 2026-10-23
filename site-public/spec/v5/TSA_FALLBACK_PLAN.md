# TSA Fallback Plan
Version: 0.1
Status: DRAFT
Date: 2026-03-24

## Purpose

Prevent single TSA dependency for RFC 3161 timestamp production.

## Current State

Primary TSA: FreeTSA (freetsa.org)
Status: active
Trust Foundation Rule 1: unchanged — timestamp MUST come from independent RFC 3161 TSA

## Trigger Conditions

- Primary TSA unreachable
- Timeout threshold exceeded
- Failed timestamp rate above threshold
- Invalid or malformed response received

## Fallback Policy

1. Primary TSA attempted first
2. On failure → secondary TSA attempted
3. TSA used is recorded in proof metadata
4. Verification relies on pack evidence, not TSA source
5. Fallback usage is logged and optionally added as seal claim

## Metadata Fields

```json
{
  "tsa_provider": "string",
  "timestamp_mode": "primary | fallback",
  "timestamp_attempt": "integer"
}
Operation Rule
Fallback usage does NOT invalidate the seal.
Fallback is recorded as an event in proof metadata.
Critical Note
"Timestamp authority may change. ISCProof offline verification
model is not affected. TSA provides independent time evidence only."
Future Actions
Select at least 1 secondary TSA
Produce at least 1 test seal with secondary TSA
Move primary/secondary config to config file
Candidate Secondary TSAs
DigiCert TSA (timestamp.digicert.com)
Sectigo TSA (timestamp.sectigo.com)
Apple TSA (timestamp.apple.com)
Status: DRAFT — implement after laptop
