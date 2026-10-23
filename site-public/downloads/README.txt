ISC website demonstration profile v1
Illustrative records, signed manifest, separate trusted signer list.
The demo key identifies this fixture, not a certified organization.
No RFC 3161 timestamp, anchor or semantic decision validation.

Build the included modified verifier:
cargo build --release --locked --manifest-path verifier-source/Cargo.toml
./verifier-source/target/release/isc_verify evidence_pack.tar --trusted-signers trusted_signers

Signer: 256 SHA256:mGXkbMgdKDIVlMv5H0QO53i4ESoP4IkZK1nbF1jRmds ISC public demonstration key (ED25519)
