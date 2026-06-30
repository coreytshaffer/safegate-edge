# SafeGate Edge Demo Run

## What this demo proves
This demo shows SafeGate’s simulated approval workflow. It proves that an approval binds to one exact canonical action hash. The original action is allowed, a mutated action is blocked, and a denied approval is blocked. Hardware attestation is reserved for a future implementation; this demo does not claim hardware-verified approval.

## Scenario
An agent requests to run `rm ./customer_exports/*.csv`. This is a high-risk action according to the loaded policy and requires human approval.
The demo simulates generating a review packet, a human approving it, and subsequent verifications against different execution attempts.

## Generated Artifacts
- **review_packet.json**: The exact payload presented to the human approver.
- **generated_approval.json**: The cryptographic approval binding the approver to the canonical hash of the action.
- **generated_denied_approval.json**: An example of a rejected request.
- **verify_original_allowed.json**: The gateway allowing the exact requested action.
- **verify_mutated_blocked.json**: The gateway blocking an action that was mutated (e.g. `rm -rf /`) after approval.
- **verify_denied_blocked.json**: The gateway blocking the original action when the approval was explicitly denied.
- **evidence_bundle/**: The full cryptographically-chained evidence bundle exported from the blocked mutation attempt.
- **demo_summary.json**: Machine-readable summary of this demo run.

## Results
- Original Decision: allowed (valid_approval)
- Mutated Decision: blocked (action_hash_mismatch)
- Denied Decision: blocked (approval_not_granted)

## Key Safety Property
The evidence bundle specifically tracks the "mutated blocked" path to prove that even if an agent has a valid approval packet, it cannot execute an action that differs from what was explicitly reviewed.

## Hardware Attestation Boundary
Policies can require hardware attestation. For this demo, hardware verification is explicitly marked as not implemented to avoid false security claims. SafeGate is hardware-ready, not hardware-verified yet.

## How to Re-run
Run the following command to regenerate this demo packet:
`python -m safegate_edge.cli demo run --output-dir examples/demo_runs/safegate_demo`
