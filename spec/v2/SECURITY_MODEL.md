# BuildSeal Security Model

## Design trade-off

Every supply-chain security system chooses from this triangle:

  broad scope
  strong trust
  few dependencies

You cannot have all three.

Sigstore: broad scope, strong trust, many dependencies.
PGP: few dependencies, complex trust model.
BuildSeal: narrow scope, few dependencies, portable.

Narrow scope is not a weakness. It is what makes offline verification possible.

## What BuildSeal guarantees

One thing only:

  This artifact was sealed by this key at this moment and has not changed since.

Nothing more.

## Security boundaries

ISCProof guarantees seal authenticity.
It does not guarantee identity, safety, or reproducibility.

BuildSeal does not prove identity.
A valid seal only proves that the signing key produced the record.
It does not prove who controls the key.

BuildSeal does not prove safety.
A sealed artifact may contain vulnerabilities or malware.
Sealing is not scanning.

BuildSeal does not prove reproducibility.
The same source may produce a different binary under different build conditions.
BuildSeal does not verify build pipelines or environments.

BuildSeal does not prove source.
A valid seal does not prove the artifact originated from the stated repository.
Commit and repo fields are metadata provided by the producer.

BuildSeal does not prove long-term validity.
If the signing key is compromised, all seals produced by that key are suspect.
This version does not include a revocation mechanism, transparency log, or trusted time anchor.

## Appropriate use

BuildSeal is appropriate for:
  release authentication in small and medium projects
  offline verification without network infrastructure
  air-gapped environments
  distributable proof that travels with the artifact
  audit evidence where cryptographic integrity is sufficient

BuildSeal is not appropriate for:
  legal or forensic chain of custody
  long-term archival with revocation guarantees
  government or defense supply chain
  environments requiring a transparency log
  proof of reproducibility

## Scope

Use Sigstore if you need a transparency log.
Use in-toto if you need build pipeline verification.
Use BuildSeal if you need offline, self-contained, portable proof.

These are not competing tools. They solve different problems.

## Summary

BuildSeal produces evidence. It does not produce compliance.
BuildSeal proves integrity. It does not prove identity.
BuildSeal is honest about what it cannot do.
