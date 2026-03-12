# ISC Verify — Binary Checksums

## v0.2.0

### isc_verify (linux/aarch64)

sha256: c488a8c9a6a60c41b65eb3ece93de5159151869e43e62edfadcade6a5350f811

Build flags:
- opt-level = 3
- lto = true
- codegen-units = 1
- strip = symbols
- panic = abort

Reproducible build:
- Source: codeberg.org/buildseal/isc-core
- Cargo.lock committed
- Build: cargo build --release
