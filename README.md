# BuildSeal

BuildSeal is a portable software integrity verification system.

It seals build artifacts into a cryptographically signed evidence pack that can be verified later without trusting the original server, repository, CI system, or BuildSeal itself.

Verification is self-contained, offline-capable, and long-term reproducible.

The goal of BuildSeal is simple:

Anyone should be able to verify
what was built,
when it was built,
and by whom it was built —

using only the artifact and the evidence pack.

No registry.
No API.
No vendor trust.
Only cryptographic proof.


## Quick start

Download verifier:

https://github.com/hakannbjk55-afk/Isc-Core/releases/download/v0.2.0/isc_verify

Make executable:
chmod +x isc_verify
Download example evidence pack:

https://verify.buildseal.io/release/seal_1772887285176_trxc9ufi

Verify:
./isc_verify evidence_pack.tar
Result:
Genuine   -> artifact matches sealed build
Modified  -> artifact differs from sealed build
## Overview

BuildSeal produces a self-contained proof bundle.

Each evidence pack contains:

- artifact hash
- signature
- build metadata (repository, commit, timestamp)
- governance key
- verification policy

Proof travels with the artifact.

Verification works:

- offline
- without API calls
- without registry
- without network access
- without trusting BuildSeal

If the evidence pack exists, verification is possible.


## Use cases

- software supply chain verification
- release integrity validation
- audit evidence packs
- reproducible build workflows
- security-sensitive environments
- air-gapped infrastructure


## Design Principles

No central trust required
Verification must work offline
Proof must be portable
Artifacts must be self-verifiable
Failure must be obvious

If verification requires trusting a server,
it is not verification.

If proof cannot be moved,
it is not proof.

If integrity cannot be checked locally,
it is not integrity.


## What BuildSeal is NOT

BuildSeal is not a CI system
BuildSeal is not a package registry
BuildSeal is not a signing service
BuildSeal is not a blockchain project

BuildSeal is a self-contained verification tool.


## Verification Engine

BuildSeal uses the ISC (Integrity Seal Chain) engine.

ISC provides:

- Ed25519 signatures
- deterministic sealing
- portable evidence packs
- policy-based verification
- offline trust model

Verification output is binary:

- Genuine
- Modified


## Independent verification

Verification does not require trusting BuildSeal.

Download verifier:

https://github.com/hakannbjk55-afk/Isc-Core/releases/download/v0.2.0/isc_verify

Example:
curl -L https://github.com/hakannbjk55-afk/Isc-Core/releases/download/v0.2.0/isc_verify -o isc_verify
chmod +x isc_verify
./isc_verify evidence_pack.tar
The result must match the web report.

If the result differs,
the artifact must not be trusted.


## License

MIT
