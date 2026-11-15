# Demo Walkthrough

The SafeGate Edge demo runs the simulated approval workflow in a single command. It checks a simulated approval against one exact canonical action hash and records why a changed action is blocked. A matching demo result is for demonstration only. Normal verification denies approval-required actions because the current packets lack authenticated approval evidence.

## Running the Demo

You can execute the entire flow by running the following command in your terminal from the project root:

```bash
python -m safegate_edge.cli demo run --output-dir examples/demo_runs/safegate_demo
```

## What Happens During the Demo?

When you run the command, the following simulated sequence occurs:

1. **Review request.** SafeGate packages the proposed action and its canonical hash in `review_packet.json`.
2. **Simulated decision.** The demo writes `generated_approval.json` and `generated_denied_approval.json` for a configured approver ID. Both packets record the action hash and policy context.
3. **Original action.** The demo verifier checks the unchanged action, the evaluated policy and the registry. It records `simulated_allowed` with reason `valid_simulated_approval` in `verify_original_allowed.json`.
4. **Changed action.** The demo verifier checks the original simulated packet against a changed request. The hash mismatch blocks the action in `verify_mutated_blocked.json`.
5. **Denied decision.** The verifier blocks the unchanged action when supplied with the denied packet and writes `verify_denied_blocked.json`.
6. **Evidence export.** The demo exports `evidence_bundle/` with the decision trace for the changed request.

## Exploring the Artifacts

The demo outputs files to `examples/demo_runs/safegate_demo/`. Key files to examine:

- **`README_DEMO.md`**: A standalone overview of the demo run you just generated.
- **`demo_summary.json`**: A machine-readable summary of the demo's assertions and results.
- **`evidence_bundle/`**: Open `evidence_manifest.json` and `observe_events.jsonl` to see how SafeGate traces the lifecycle of an intercepted threat.
