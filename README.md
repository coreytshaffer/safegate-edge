# SafeGate Edge

SafeGate Edge is a local approval gateway for AI agents and automation workflows. It blocks high-risk actions until a human physically approves the exact action, then creates verifiable evidence showing what was requested, what was approved, what changed, and whether execution was allowed or blocked.

> **MFA verifies identity. SafeGate verifies the action.**

SafeGate currently supports simulated approval packets for deterministic demos and tests. SGE-007 introduces the boundary where future hardware-backed approvals will plug in. Policies can mark an action as requiring hardware attestation, but real hardware attestation verification is not yet implemented.
SafeGate is hardware-ready, not hardware-verified yet.

## Concepts

### The Canonical Action Hash
SafeGate enforces deterministic safety by hashing every action request into a strict canonical format. A human approver signs this hash. If the agent changes *anything*—even reordering keys or changing whitespace in a way that alters the canonical representation—the hash changes and the approval is rejected.

The canonical representation ensures:
- Consistent key ordering
- No extraneous whitespace
- Deterministic payload structure

The resulting byte string is then hashed using SHA-256, and prefixed with `sha256:` to produce the final digest (e.g., `sha256:abcd...`).

## Quickstart: End-to-End Demo

Run the end-to-end demo to see SafeGate in action:

```bash
python -m safegate_edge.cli demo run --output-dir examples/demo_runs/safegate_demo
```

The demo creates a human review packet, generates approved and denied approval packets, verifies the original action, verifies a mutated action, verifies a denied approval, and exports a reviewer-facing evidence bundle.

## Documentation

- **[Reviewer Packet](docs/reviewer_packet.md)**: High-level overview of what this prototype proves.
- **[Demo Walkthrough](docs/demo_walkthrough.md)**: Step-by-step guide to the demo artifacts.
- **[Architecture](docs/architecture.md)**: System design and verification loop.
- **[Threat Model](docs/threat_model.md)**: Detailed breakdown of in-scope protections and out-of-scope boundaries.
- **[Limitations](docs/limitations.md)**: Honest accounting of the prototype's current state.
- **[Release Notes](docs/release_notes.md)**: Changelog and milestones.

## Usage

The SafeGate CLI allows you to compute hashes, generate reviews, and verify approvals.

### 1. Compute a Hash
```bash
safegate hash --action examples/action_requests/delete_customer_exports_original.json
```

### 2. Verify an Approved Action
If the action matches the approval packet, the verification will succeed (decision: `allowed`):
```bash
safegate verify \
  --action examples/action_requests/delete_customer_exports_original.json \
  --approval examples/approval_packets/valid_approval.json
```

### 3. Block a Mutated Action
If the action has been tampered with (e.g., the command was changed to `rm -rf`), the hash will not match the approval, and SafeGate will block it (decision: `blocked`):
```bash
safegate verify \
  --action examples/action_requests/delete_customer_exports_mutated.json \
  --approval examples/approval_packets/valid_approval.json
```


## SafeGate Observe

SafeGate Observe provides an append-only verifiable event trace for every verification decision. It exports an EvidenceBundle containing the original request, the approval, the verification result, the execution decision, and a JSONL event trace where each event is cryptographically hashed and linked to the previous event (forming a hash chain). An evidence manifest includes file-level SHA-256 hashes to guarantee the bundle's integrity.

### 3. Human Review Packets

SafeGate review packets show the exact action a human is being asked to approve. Each packet includes the plain-language summary, raw action details, policy rule, approval requirement, expiration, and canonical action hash.

The human does not approve a vague request. The human reviews and approves a specific action hash.

Generate a review packet:
```bash
python -m safegate_edge.cli review create --action action_request.json --policy default_policy.json --output review_packet.json
```

### 4. Approval Packet Generation

SafeGate can now simulate the human approval step. A pending review packet can be converted into an approval packet by an active approver. The approval packet binds the approver, review_id, action_id, policy rule, and canonical action_hash into the artifact later used by the verifier.

The approval does not approve a general intent. It approves one reviewed action hash.

Generate an approval packet:
```bash
python -m safegate_edge.cli approve create --review review_packet.json --approver corey --status approved --output generated_approval.json
```

### 5. Self-Diagnostic Commands

SafeGate Edge includes self-diagnostic tools to ensure the environment is healthy and configurations are valid before you trust it in production.

### Doctor
The `doctor` command inspects the SafeGate environment, checking for core module imports, policy availability, approver registry validity, writable output directories, and recomputing fixture hashes.

```bash
safegate doctor
```
An example of a healthy output:
```text
[PASS]  SafeGate core modules importable
[PASS]  Default policy available
[PASS]  Examples directory exists
...
Doctor check complete.
```

### Preflight
The `preflight` command tests a specific action request against your configurations to verify it parses correctly, the schema is valid, the risk level is recognized, and whether an active approver is available if the policy requires approval.

```bash
safegate preflight --action examples/action_requests/delete_customer_exports_original.json
```

### Approver Registry
SafeGate uses a simple JSON-based approver registry (e.g. `examples/config/approvers.json`) to keep track of active approvers. 
```json
{
  "schema_version": "approvers.v1",
  "approvers": [
    {
      "approver_id": "corey",
      "display_name": "Corey",
      "status": "active",
      "approval_methods": ["placeholder_security_key"]
    }
  ]
}
```
The `doctor` and `preflight` tools will automatically validate this registry.