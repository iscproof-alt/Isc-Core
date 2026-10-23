# ISC site demonstration: isc-site-demo-v1

Verifier: based on v0.2.0, with local fixes and --trusted-signers support.
Use the exact source snapshot in the demonstration kit.

Linux x86-64 executable: dynamically linked; glibc >= 2.34 plus compatible system libraries.

| Artifact | SHA-256 |
| --- | --- |
| evidence_pack.tar | 6d2f1df5bba377f7d4dd3f0d03876fa652ad4d5ba480f260b1f42f32a91d16aa |
| isc_verify-linux-x86_64 | 1ce8f450a584f73a63506c1db449fdda25e90111075c68ae3ca67970dc7eb863 |
| verifier-source/src/main.rs | 73120eb4b9aae0b26700d3aad1f222b05f9711a538f75d48755e6dc885a848ad |

Demo signer: 256 SHA256:mGXkbMgdKDIVlMv5H0QO53i4ESoP4IkZK1nbF1jRmds ISC public demonstration key (ED25519)

## Internal test results

- valid: expected PACK VERIFIED; exit 0; PASS
- changed-content: expected HASH_MISMATCH; exit 1; PASS
- missing-file: expected MISSING_FILE; exit 1; PASS
- missing-signature: expected MISSING_FILE; exit 1; PASS
- rewritten-manifest: expected SIGNATURE_INVALID; exit 1; PASS

These are project-run results, not an independent audit. No RFC 3161 timestamp,
blockchain anchor or semantic relationship verification is included in this example.
The TAR archive checksum is not the verifier's internal package-identity calculation.
The demo signer list is not independent issuer-identity certification.
Building from source with --locked avoids trusting the prebuilt executable;
it still relies on source, toolchain and dependencies.
