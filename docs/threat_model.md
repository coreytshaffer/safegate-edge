# Threat Model

SafeGate Edge checks action requests against policy. The calling application enforces the verifier's decision.

## Verification Checks

- **Changed action.** Verification blocks a packet whose recorded hash differs from the canonical hash of the attempted action.
- **Missing authenticated approval.** Normal verification denies approval-required actions. Current packets lack authenticated approval evidence.
- **Denied approval.** Verification blocks packets with `denied` status, including during simulation.
- **Mismatched policy or registry context.** The verifier checks the evaluated policy ID, rule ID and approval requirement. It also checks that the named approver is active and that the caller's registry permits the packet's method.
- **Missing or invalid policy**: If the system cannot resolve a valid policy, it fails closed to prevent un-governed execution.
- **Unknown risk levels**: Any action lacking a clear risk definition is treated as a critical anomaly and blocked.
- **Stale or expired approvals**: Configurable time bounds ensure approvals cannot be hoarded and used indefinitely.
- **Opaque automation without evidence**: The event logger exports a cryptographically-chained evidence bundle, ensuring every decision is auditable and tamper-evident.

## Out of Scope: Current Prototype Limitations

This is a prototype spine. The following threats are intentionally out of scope for this version:

- **Authenticated approval.** The explicit demo can report a matching simulated approval for demonstration only. Execution authorization for actions requiring approval depends on authenticated evidence. Verifying real hardware-backed evidence is future work.
- **Registry custody.** The caller controls the registered approver IDs and permitted methods. Integration with an identity provider and administration of the registry are outside the prototype.
- **Compromised local machine / Python runtime**: If the underlying host operating system or Python environment running SafeGate is compromised, an attacker can bypass the verification hooks entirely.
- **Signed release artifacts**: The SafeGate source code itself is not currently distributed via signed artifacts, meaning supply chain attacks against the installation are possible.
- **Networked approval service**: Approvals are currently generated as local JSON artifacts rather than through a centralized, network-isolated identity provider.
- **Production IAM integration**: The approver registry is a static JSON file, not integrated with Okta, Active Directory, or Google Workspace.
- **Real command execution enforcement**: SafeGate acts as an interceptor library; it relies on the executing agent to honor the `blocked` decision rather than acting as a kernel-level sandbox.
