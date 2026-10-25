ISC website verifier 0.2.1
Source commit: 4d5c74ebe91a5369d98d1d9debb4bcd6adc7c650
Source tree: https://github.com/iscproof-alt/Isc-Core/tree/4d5c74ebe91a5369d98d1d9debb4bcd6adc7c650/demos/site_v1/verifier-source

This version replaces the earlier v0.2.0-based snapshot for the website fixture.
This is not the BuildSeal hosted 5.1 verifier. Compatibility is not established.

Prebuilt executable: Linux x86-64; GLIBC symbol versions through 2.34; compatible loader and system libraries required.
This does not establish portability to every distribution or native Windows/macOS.
Build from reviewed source using Rust and Cargo:
  cargo build --release --locked --manifest-path verifier-source/Cargo.toml
  ./verifier-source/target/release/isc_verify evidence_pack.tar --trusted-signers trusted_signers

Before chmod/execution, check the executable, package and trust-list SHA-256
against the release note in the source repository and the website.
The same operator controls both channels; these are not independent certification.
Inspect the source and choose whether to trust the externally supplied signer key.

The kit excludes the prebuilt executable. --locked locks dependency resolution;
it is not a reproducible-build or software-correctness guarantee.
No RFC3161 TSA, decision correctness, or semantic record-chain guarantee is provided.

The regression suite rejects an unchanged, genuinely signed original package
when its signing key is excluded from the external trust list. It also checks
unlisted files, traversal, symlinks, hardlinks, duplicate entries and malformed manifests.
Only manifest files and the detached manifest signature are envelope exceptions;
other regular files must be explicitly listed and hash-checked.
