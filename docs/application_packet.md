# SafeGate Edge: Application & Demo Packet

## 1-Paragraph Product Summary

SafeGate Edge is a local, verifiable approval boundary for high-risk AI and automation actions. Standard IAM tools focus on *who* is allowed to act; SafeGate focuses on *what exact action* is being approved. It converts an action request into a deterministic canonical hash, generates a human review packet, creates a hash-bound approval or denial packet, and verifies that the attempted action still matches the approved hash before allowing it. If the action changes after approval, SafeGate fails closed. Every decision is exported as a tamper-evident evidence bundle so reviewers can inspect what was requested, what was approved, what was attempted, and why the action was allowed or blocked.

## What the Demo Proves

* **Canonical action hashing:** SafeGate produces a deterministic cryptographic hash for the exact action request, avoiding drift from JSON formatting differences.
* **Human review contract:** SafeGate generates a review packet showing the plain-language action summary, raw action details, policy rule, expiration, and canonical action hash.
* **Hash-bound approval:** An approval packet binds an active approver, review ID, policy rule, action ID, and canonical action hash into one verifiable artifact.
* **Fail-closed mutation blocking:** If the attempted action changes after approval, SafeGate detects the hash mismatch and blocks the action.
* **Denied approval blocking:** A denied approval packet cannot be treated as permission.
* **Policy-bound verification:** SafeGate only allows approval-free actions when a valid policy explicitly says approval is not required.
* **Tamper-evident evidence:** The demo exports a hash-linked evidence bundle showing the decision trace from review through verification.

## 90-Second Pitch Script

We want AI agents and automation tools to handle more complex work, but we cannot let them unilaterally run destructive commands or mutate high-risk actions after approval.

SafeGate Edge is a local approval gateway for that problem. When an agent proposes a high-risk action, SafeGate turns the request into a canonical action hash and generates a human review packet. The human is not approving a vague intent. They are reviewing a specific action, policy rule, expiration window, and hash.

If an active approver generates an approval packet, that approval is bound to the exact reviewed action hash. When execution is attempted, SafeGate verifies the current action against the approval. If the action is unchanged, it can proceed. If the command or target changes, the hash no longer matches, and SafeGate blocks the action. If the approver denied the request, SafeGate blocks that too.

The result is a simple safety boundary for agentic systems: approve one exact action, fail closed if it changes, and export the evidence. The current prototype uses simulated approval packets and is hardware-ready, not hardware-verified yet. The next milestone is real hardware-backed approval using security keys or platform attestation.

## Repo Quickstart

Clone the repository and run the end-to-end demo:

```bash
git clone <repository_url>
cd safegate_edge
python -m safegate_edge.cli demo run --output-dir examples/demo_runs/safegate_demo
```

The demo creates:

```text
review_packet.json
generated_approval.json
generated_denied_approval.json
verify_original_allowed.json
verify_mutated_blocked.json
verify_denied_blocked.json
demo_summary.json
README_DEMO.md
evidence_bundle/
```

The key result:

```text
original action + valid approval -> allowed / valid_approval
mutated action + same approval -> blocked / action_hash_mismatch
original action + denied approval -> blocked / approval_not_granted
```

## Current Limitations

* **Hardware attestation is not implemented yet:** SafeGate is hardware-ready, not hardware-verified. The current demo uses simulated approval packets. Policies can reserve space for hardware attestation, but SafeGate does not yet verify YubiKey, WebAuthn, TPM, Secure Enclave, or passkey evidence.
* **Approver identity is local and static:** The approver registry is currently a JSON configuration file, not a production identity provider integration.
* **No kernel-level sandboxing:** SafeGate is currently a verifier and approval gateway. It relies on an agent framework, wrapper, CI step, or automation layer to call it before execution.
* **No production signing chain yet:** The prototype uses canonical hashes and tamper-evident evidence records, but not a full signed release or remote attestation chain.
* **Prototype evidence, not certification:** The demo proves the control-plane pattern. It does not certify production security.

## Next Milestone

**Real Hardware-Backed Approval**

The next milestone is replacing simulated approvals with real hardware-backed approval evidence. Candidate paths include FIDO2/WebAuthn, YubiKey/PIV, TPM-backed signing, platform secure enclaves, or passkey-style human-presence verification.

The goal is to move from:

```text
hash-bound simulated approval
```

to:

```text
hash-bound approval with verifiable human presence
```

That would turn SafeGate from a deterministic prototype into a stronger real-world approval boundary for high-risk AI and automation actions.
