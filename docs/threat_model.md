# Threat Model

SafeGate Edge is designed to enforce deterministic boundaries around autonomous agent actions. It is crucial to understand what the system protects against and what remains out of scope for the current prototype.

## In Scope: What SafeGate Protects Against

SafeGate Edge successfully mitigates the following threats:

- **Action mutation after approval**: If an agent requests approval for a safe command but subsequently attempts to execute a malicious command, the canonical hash mismatch triggers a hard block.
- **Approval reuse against changed action content**: An approval is cryptographically bound to a single canonical payload; it cannot be applied to any other action request.
- **Missing approval for approval-required actions**: Actions flagged by the policy engine as requiring approval will fail closed if no valid approval packet is supplied.
- **Denied approval being treated as permission**: A human denial cryptographically binds to a `denied` status. The verifier will explicitly block the action.
- **Missing or invalid policy**: If the system cannot resolve a valid policy, it fails closed to prevent un-governed execution.
- **Unknown risk levels**: Any action lacking a clear risk definition is treated as a critical anomaly and blocked.
- **Stale or expired approvals**: Configurable time bounds ensure approvals cannot be hoarded and used indefinitely.
- **Opaque automation without evidence**: The event logger exports a cryptographically-chained evidence bundle, ensuring every decision is auditable and tamper-evident.

## Out of Scope: Current Prototype Limitations

This is a prototype spine. The following threats are intentionally out of scope for this version:

- **Real hardware attestation verification**: SafeGate is hardware-ready, not hardware-verified yet. Policies can require hardware keys, but the cryptographic verification of YubiKeys or Secure Enclaves is currently stubbed/simulated.
- **Malicious active approvers**: The system trusts the approvers defined in the registry. It does not protect against a registered approver intentionally signing off on malicious actions.
- **Compromised local machine / Python runtime**: If the underlying host operating system or Python environment running SafeGate is compromised, an attacker can bypass the verification hooks entirely.
- **Signed release artifacts**: The SafeGate source code itself is not currently distributed via signed artifacts, meaning supply chain attacks against the installation are possible.
- **Networked approval service**: Approvals are currently generated as local JSON artifacts rather than through a centralized, network-isolated identity provider.
- **Production IAM integration**: The approver registry is a static JSON file, not integrated with Okta, Active Directory, or Google Workspace.
- **Real command execution enforcement**: SafeGate acts as an interceptor library; it relies on the executing agent to honor the `blocked` decision rather than acting as a kernel-level sandbox.
