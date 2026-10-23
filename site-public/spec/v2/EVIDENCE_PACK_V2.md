# Evidence Pack Format v2

This document defines the structure of an ISC evidence pack version 2.


## Pack structure

An evidence pack is a tar archive containing:

- manifest.json
- signature.sig
- public_key.pem

The artifact itself is not required to be inside the pack.
Verification uses the artifact provided by the user.


## manifest.json

Required fields:

    pack_version: 2
    signature_version: 1
    tool_version: string
    sealed_at: RFC3339 timestamp
    os: string
    arch: string
    artifact_name: string
    artifact_sha256: hex
    repo: string
    commit: string
    producer_fingerprint: string


## Field rules

pack_version
Format version of the pack. Must be 2.

signature_version
Signature format version.

tool_version
Version of the tool that created the pack.

sealed_at
Timestamp when the pack was created. Must be UTC, format: 2006-01-02T15:04:05Z

os
Target operating system.

arch
Target architecture.

artifact_name
Name of the artifact file.

artifact_sha256
SHA256 hash of the artifact.

repo
Repository identifier.

commit
Commit identifier.

producer_fingerprint
Fingerprint of the signing key.


## Signature

signature.sig contains the Ed25519 signature of manifest.json.

public_key.pem must be used to verify the signature.


## Verification rules

Verification must:

- read manifest.json
- verify signature.sig using public_key.pem
- compute SHA256 of the artifact
- compare with artifact_sha256
- fail if any mismatch occurs

Verification must work offline.
Verification must not require any external service.


## Compatibility

Future versions may add fields.

Unknown fields must be ignored.

pack_version defines compatibility.

Unsupported pack_version must cause verification failure.
