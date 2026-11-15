# Demo Recording Script (90-Second)

## Setup
Ensure your terminal is clear and you are in the project root (`safegate_edge`).

## Script

**[0–10s: Problem]**
*(Terminal is empty, ready for command)*
"We want AI agents to execute complex tasks, but we can't let them unilaterally run destructive commands or mutate high-risk actions after approval."

**[10–25s: What SafeGate does]**
"SafeGate Edge checks an agent's proposed action against policy. It records the specific action and its canonical hash in a review packet. Normal verification denies actions that require approval because the current packets lack authenticated approval evidence."

**[25–45s: Run demo command]**
*(Type and run the command)*
```bash
python -m safegate_edge.cli demo run --output-dir examples/demo_runs/safegate_demo
```
"The demo generates a review packet, records a simulated decision for its action hash, and checks the result."

**[45–65s: Show demo_summary.json results]**
*(Print or open the summary file)*
```bash
cat examples/demo_runs/safegate_demo/demo_summary.json
```
"The unchanged action passes the checks in this explicit demo. That result is for demonstration only. The changed request fails because the action hashes differ. The verifier also blocks a denied packet."

**[65–80s: Explain evidence bundle]**
*(Show the evidence bundle files)*
```bash
ls examples/demo_runs/safegate_demo/evidence_bundle/
```
"The evidence bundle records the decision trace for the changed request, including why verification blocked it."

**[80–90s: Hardware boundary / next milestone]**
"The demo shows how SafeGate compares one canonical action hash with the recorded decision. Approval-required actions need authenticated evidence before execution. Hardware-backed verification is future work."
