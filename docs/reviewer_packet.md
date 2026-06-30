# Reviewer Packet

## What is SafeGate Edge?
SafeGate Edge is a local, verifiable safety boundary for autonomous agents. It acts as an interceptor between an agent’s requested action (like executing a shell command or making an API call) and the actual execution of that action. 

SafeGate Edge demonstrates a local approval gateway where a human reviews one exact canonical action hash, an active approver generates an approval packet, the original action is allowed, changed actions fail closed, denied approvals fail closed, and the full decision trace is exported as tamper-evident evidence.

## Core Capabilities
- **Canonical Hashing**: Deterministically hashes all inputs to ensure that the action reviewed by the human is cryptographically identical to the action being executed by the agent.
- **Policy Enforcement**: Enforces risk-based rules on actions (e.g., automatically allowing low-risk actions while blocking high-risk actions pending human approval).
- **Human Review Contract**: Connects directly with a registered human approver, ensuring that decisions are explicitly signed off by verified personnel.
- **Immutable Evidence**: Generates a cryptographically-chained event log of the entire decision lifecycle, allowing any party to audit exactly why an action was allowed or blocked.

## Navigating the Prototype
If you are evaluating this prototype, we recommend the following path:
1. Start with the **[End-to-End Demo Walkthrough](demo_walkthrough.md)**. You can run the demo yourself locally with one command.
2. Read the **[Architecture](architecture.md)** to understand how the components fit together.
3. Review the **[Threat Model](threat_model.md)** to understand exactly what this system protects against.
4. Check the **[Limitations](limitations.md)** to understand the boundaries of this prototype and its future trajectory.
