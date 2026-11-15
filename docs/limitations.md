# Limitations

SafeGate Edge is a prototype for verifying an action against policy and its canonical hash. Normal verification denies approval-required actions because the current packet format lacks authenticated approval evidence.

## Hardware Attestation

Policies can require hardware-backed approval. Verification of FIDO2/WebAuthn signatures, TPM attestation and other hardware evidence is future work.

## Identity and Authentication

The caller supplies a JSON approver registry. The verifier uses it to check active status and permitted approval methods. Cryptographic authentication of the person named in a packet requires additional evidence.

## Runtime Isolation

SafeGate acts as an interceptor library. It relies on the executing agent framework to actively call the `verifier` before executing commands. It is not a kernel-level sandbox (like gVisor or AppArmor) and cannot force a rogue Python process to verify its actions. If the Python runtime itself is compromised, the verification hooks can be bypassed.

## Evidence Tampering

While the evidence bundle is cryptographically chained and tamper-evident, it is currently written to local disk. A root-level compromise of the local machine could theoretically overwrite the logs before they are exported to an append-only remote storage bucket.

## Summary

The explicit demo can report a successful simulated match for one canonical action hash. Use that result to evaluate the verification flow. Execution authorization for approval-required actions requires authenticated approval evidence.
