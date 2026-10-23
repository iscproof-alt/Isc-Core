# ISCProof — verifiable decision records

When a decision is questioned, show the record—and check that its packaged files have not changed since the manifest was signed.

ISCProof describes evidence formats and verification workflows. This repository includes protocol specifications, packers, verifiers and demonstration material. BuildSeal is a related product that issues ISCProof-compatible evidence.

**Start here:** [Inspect the example](https://www.iscproof.io/#example) · [Download and verify](https://www.iscproof.io/#downloads) · [Look up a Proof ID](https://www.iscproof.io/verify) · [Demo checksums and test results](docs/releases/isc-site-demo-v1.md)

## What the published demonstration checks

The `isc-site-demo-v1` profile contains three illustrative decision/policy records and a signed file manifest. These are demonstration records, not customer data or a live AI execution.

The included verifier checks file hashes against the manifest and verifies the manifest signature against an explicitly supplied demo signer key. It rejects the four tested forms of incomplete or modified evidence below.

It does **not** establish:

- Whether the recorded facts were accurate or the policy was actually in force.
- Whether a decision was correct or justified.
- The meaning or validity of the links between records.
- When the package was created or signed: this demonstration has no RFC 3161 timestamp or blockchain anchor. Dates in the files are signer-stated.
- An independently certified issuer identity: the supplied key identifies the public demonstration.

The verifier's internal package-identity calculation is separate from the SHA-256 checksum of the downloadable TAR archive.

## Verify locally

The demonstration uses a verifier based on **v0.2.0 with local fixes and `--trusted-signers` support**. Use the exact included source snapshot rather than assuming that another v0.2.0 executable is identical.

### Build from the included source

Rust and Cargo are required. From this repository:

```bash
cargo build --release --locked --manifest-path demos/site_v1/verifier-source/Cargo.toml
./demos/site_v1/verifier-source/target/release/isc_verify \
  demos/site_v1/evidence_pack.tar \
  --trusted-signers demos/site_v1/trusted_signers
```

Expected successful result: `PACK VERIFIED`, exit code `0`.

After extracting the [downloadable kit](https://www.iscproof.io/downloads/isc-demo-kit.zip), the same source is under `verifier-source/`, with the package and signer list in the kit's root directory.

Building with `--locked` avoids relying on the prebuilt executable and preserves dependency resolution. It still relies on the source, compiler and dependencies; it is not a guarantee of correctness or reproducible binary output. The initial build may need network access to obtain dependencies.

### Use the prebuilt Linux executable

The [published executable](https://www.iscproof.io/downloads/isc_verify-linux-x86_64) is for **Linux x86-64**, dynamically linked, and requires **glibc 2.34 or later** and compatible system libraries. It is not a Windows or macOS executable.

From a checkout containing the published website files:

```bash
chmod +x site-public/downloads/isc_verify-linux-x86_64
./site-public/downloads/isc_verify-linux-x86_64 \
  site-public/downloads/evidence_pack.tar \
  --trusted-signers site-public/downloads/trusted_signers
```

Compare the executable, archive and verifier-source hashes with the [published checksum note](docs/releases/isc-site-demo-v1.md). The website and repository are project-controlled distribution channels, not independent certification. For another issuer's evidence, obtain the expected signer key through a channel you trust.

## Published internal tests

| Case | Expected result | Exit |
| --- | --- | --- |
| `valid` | `PACK VERIFIED` | 0 |
| `changed-content` | `HASH_MISMATCH` | 1 |
| `missing-file` | `MISSING_FILE` | 1 |
| `missing-signature` | `MISSING_FILE` | 1 |
| `rewritten-manifest` | `SIGNATURE_INVALID` | 1 |

These are five project-run fixture cases: one acceptance case and four rejection cases. The [report](demos/site_v1/report.json) and individual logs record those results. They are not a third-party audit or a general conformance certification.

## Hosted Proof ID lookup

[The website lookup](https://www.iscproof.io/verify) displays a result returned by a hosted service. The browser does not independently verify the package. For independent checking, use the applicable package, verifier and expected signer key.

The hosted service and other protocol versions may expose checks beyond this demonstration. Their results and trust requirements must be evaluated separately; this fixture does not demonstrate the full ISCProof stack.

## Repository map

| Path | Purpose |
| --- | --- |
| `site-public/` | Published static website and curated public downloads |
| `demos/site_v1/` | Signed demonstration, exact source snapshot and recorded test outputs |
| `isc_verify/` | Standalone verifier source aligned with the demonstration snapshot |
| `docs/releases/isc-site-demo-v1.md` | Demo hashes, compatibility information and test summary |
| `spec/` | Protocol and format documents; consult each document's version and scope |
| `docs/` | Architecture, security and supporting documentation |

Older packers, verifier versions and fixtures are retained as historical or separate development material. They are not interchangeable with the current demo profile merely because they share the ISC name.

## Maintenance and integration

Maintained by Hakan Ünal. For technical questions or integration discussions, [open an issue](https://github.com/iscproof-alt/Isc-Core/issues).

Bring one decision flow. We can identify what the proposed evidence can attest to, what must be trusted externally and what remains outside verification.

## License

See [LICENSE](LICENSE). The repository currently states **All Rights Reserved** and is published for review and discussion. Public visibility does not grant an MIT license or unrestricted rights to use or redistribute the software. This documentation update does not change the license.
