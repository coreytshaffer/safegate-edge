# Reviewer Packet

## What is SafeGate Edge?
SafeGate Edge is a local verifier for actions proposed by autonomous agents. Normal verification denies approval-required actions because the current packets lack authenticated approval evidence. The explicit demo can report a matching simulated approval for demonstration only. It blocks changed actions and denied packets and exports the decision trace for a changed action.

## Core Capabilities
- **Canonical hashing.** Compares the action's computed hash with the hash in the packet.
- **Policy verification.** Evaluates the risk rule and compares the policy ID, rule ID and approval requirement with the packet.
- **Registry checks.** Checks the named approver's active status and the packet method against the caller-configured registry. Execution authorization for approval-required actions requires authenticated approval evidence.
- **Decision trace.** The demo exports a hash-linked event log for the changed request.

## Navigating the Prototype
If you are evaluating this prototype, we recommend the following path:
1. Start with the **[End-to-End Demo Walkthrough](demo_walkthrough.md)**. You can run the demo yourself locally with one command.
2. Read the **[Architecture](architecture.md)** to understand how the components fit together.
3. Review the **[Threat Model](threat_model.md)** to understand exactly what this system protects against.
4. Check the **[Limitations](limitations.md)** to understand the boundaries of this prototype and its future trajectory.
