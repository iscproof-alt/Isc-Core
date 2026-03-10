# Security Model

BuildSeal is an evidence system.
It guarantees integrity of artifacts and traceability of sealing events.
It does not guarantee identity, safety, or compliance by itself.

## Guarantees

BuildSeal guarantees the following:

### Integrity
The artifact has not changed since it was sealed.

### Sealing time
The evidence pack contains the timestamp of sealing (sealed_at).

### Signature validity
The evidence pack was signed by the key that produced the signature.

### Evidence consistency
The artifact, metadata, and signature belong to the same evidence pack.

## Non-Guarantees

BuildSeal does NOT guarantee the following:

### Authorship ⚠️
BuildSeal verifies the key, not the person.
Who owns the key is outside the scope.

### Reproducibility ❌
BuildSeal does not guarantee that the build environment was clean
or that the artifact can be reproduced.

### Code safety ❌
BuildSeal does not verify that the code is secure, correct, or trusted.

### Compliance ❌
BuildSeal produces verifiable evidence.
It does not by itself make a system compliant.

---

> BuildSeal produces evidence. It does not produce compliance.
