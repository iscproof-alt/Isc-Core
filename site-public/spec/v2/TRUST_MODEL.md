# Trust Model

BuildSeal separates verification from identity discovery.
Verification is fully offline.
Identity can be established using different trust anchors, depending on the environment.

## What a sealed release contains

- artifact hash
- producer fingerprint
- signature
- manifest metadata

## What verification guarantees

The verifier checks the pack using only the public key.
No server, no transparency log, no internet connection is required.

This guarantees:
- the artifact was not modified
- the pack was signed by the holder of the private key
- the manifest matches the artifact

## What verification does not answer

Verification alone does not answer:

> Who owns this key?

This is the identity bootstrap problem.

## Identity bootstrap

BuildSeal does not enforce a single global identity system.
Instead, it allows multiple trust anchors.

### Level 0 — Manual fingerprint pinning

The public key fingerprint is shared through a trusted channel:
documentation, audit report, secure message, or in-person exchange.

### Level 1 — DNS identity (recommended)

A domain can publish a fingerprint using a TXT record.

Example:

    buildseal.io TXT
    v=ISC1 fingerprint=18a0172956d820f8

The verifier can check that the domain declares this key.
This proves domain control, not personal identity.

### Level 2 — Profile / repository proof

A maintainer may publish the fingerprint in:
- GitHub profile
- Codeberg profile
- project website
- release notes

This provides social or organizational proof.

### Level 3 — External identity systems (optional)

OIDC, transparency logs, or other identity providers can be used
on top of BuildSeal, but are not required for verification.

## Design principle

Sigstore trusts the internet.
BuildSeal trusts the pack.

Verification must work offline.
Identity must remain flexible.

Different environments require different trust models:
- air-gapped systems
- audits
- regulated deployments
- open source distribution
- internal CI/CD

BuildSeal keeps verification minimal,
and lets users choose how to trust the key.
