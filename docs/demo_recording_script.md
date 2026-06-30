# Demo Recording Script (90-Second)

## Setup
Ensure your terminal is clear and you are in the project root (`safegate_edge`).

## Script

**[0–10s: Problem]**
*(Terminal is empty, ready for command)*
"We want AI agents to execute complex tasks, but we can't let them unilaterally run destructive commands or mutate high-risk actions after approval."

**[10–25s: What SafeGate does]**
"SafeGate Edge is a local approval gateway. When an agent proposes a high-risk action, SafeGate turns the request into a canonical action hash and asks a human for approval. The human is not approving a vague intent—they are reviewing a specific action and hash."

**[25–45s: Run demo command]**
*(Type and run the command)*
```bash
python -m safegate_edge.cli demo run --output-dir examples/demo_runs/safegate_demo
```
"Let's run the end-to-end demo. This simulates the entire lifecycle: generating a review packet, simulating an approval bound to the exact canonical hash, and verifying execution."

**[45–65s: Show demo_summary.json results]**
*(Print or open the summary file)*
```bash
cat examples/demo_runs/safegate_demo/demo_summary.json
```
"As you can see, when the agent tries to execute the original, unchanged action, SafeGate allows it. But if the agent attempts a mutated action using the exact same approval, the canonical hash breaks and SafeGate blocks it immediately. A denied approval is also blocked."

**[65–80s: Explain evidence bundle]**
*(Show the evidence bundle files)*
```bash
ls examples/demo_runs/safegate_demo/evidence_bundle/
```
"Every decision generates a tamper-evident evidence bundle. This hash-linked trace proves to auditors exactly what was requested, what was approved, what was attempted, and why the action was intercepted."

**[80–90s: Hardware boundary / next milestone]**
"This prototype uses simulated approval packets. The safety property being demonstrated is that approval binds to one exact canonical action hash. Hardware-backed human presence is the next milestone."
