# Limitations

SafeGate Edge is currently a functional, deterministic prototype demonstrating the core mechanics of a secure agent approval flow. It proves the *mechanics* of verification, but not the *infrastructure* of security.

## Hardware Attestation

**SafeGate is hardware-ready, not hardware-verified yet.** 

While the policy engine can require hardware security keys, and the verifier will block requests that lack them when required, the system does not yet perform real cryptographic verification of hardware tokens (e.g., FIDO2/WebAuthn signatures or TPM attestation). The `hardware_security_key` approval method is reserved for future implementation.

## Identity and Authentication

The approver registry is currently a static JSON file (`approvers.json`). It is not integrated with a real Identity Provider (IdP) like Okta or Active Directory. It simulates identity rather than cryptographically verifying a user session.

## Runtime Isolation

SafeGate acts as an interceptor library. It relies on the executing agent framework to actively call the `verifier` before executing commands. It is not a kernel-level sandbox (like gVisor or AppArmor) and cannot force a rogue Python process to verify its actions. If the Python runtime itself is compromised, the verification hooks can be bypassed.

## Evidence Tampering

While the evidence bundle is cryptographically chained and tamper-evident, it is currently written to local disk. A root-level compromise of the local machine could theoretically overwrite the logs before they are exported to an append-only remote storage bucket.

## Summary

This prototype proves that **if** an agent calls the gate, and **if** the approval signatures are valid, the action is cryptographically constrained to its approved intent. The next phases of development will focus on replacing the simulated trust anchors with real cryptographic identity and hardware isolation.
