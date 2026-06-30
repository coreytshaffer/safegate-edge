# Demo Walkthrough

The SafeGate Edge End-to-End Demo is a deterministic runner that executes the entire decision lifecycle in a single command. It proves that an approval binds to one exact canonical action hash and that mutated requests are reliably blocked.

## Running the Demo

You can execute the entire flow by running the following command in your terminal from the project root:

```bash
python -m safegate_edge.cli demo run --output-dir examples/demo_runs/safegate_demo
```

## What Happens During the Demo?

When you run the command, the following simulated sequence occurs:

1. **Review Request Generation**: An agent requests to run a destructive command (`rm ./customer_exports/*.csv`). SafeGate packages this into a `review_packet.json`.
2. **Approval Simulation**: A simulated human approver reviews the packet and grants approval, generating a cryptographically signed `generated_approval.json`. A rejected approval is also generated (`generated_denied_approval.json`) for completeness.
3. **Original Action Verification**: The agent attempts to execute the exact action that was approved. SafeGate verifies the canonical hash and **allows** the action (`verify_original_allowed.json`).
4. **Mutated Action Verification**: The agent attempts to execute a *mutated* action (`rm -rf /`) using the *original* approval packet. SafeGate computes the canonical hash, detects the mismatch, and **blocks** the action (`verify_mutated_blocked.json`).
5. **Denied Approval Verification**: The agent attempts to execute the original action, but the approval was denied. SafeGate reads the denial and **blocks** the action (`verify_denied_blocked.json`).
6. **Evidence Export**: SafeGate exports a tamper-evident, cryptographically chained `evidence_bundle/` documenting the complete lifecycle of the mutated blocked path. This proves to auditors exactly why the action was blocked.

## Exploring the Artifacts

The demo outputs files to `examples/demo_runs/safegate_demo/`. Key files to examine:

- **`README_DEMO.md`**: A standalone overview of the demo run you just generated.
- **`demo_summary.json`**: A machine-readable summary of the demo's assertions and results.
- **`evidence_bundle/`**: Open `evidence_manifest.json` and `observe_events.jsonl` to see how SafeGate traces the lifecycle of an intercepted threat.
