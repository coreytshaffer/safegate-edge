# Architecture Overview

SafeGate Edge checks action requests in stages. The calling application decides whether to submit a request and is responsible for enforcing the verification result.

## The Spine

1. **Gate.** The calling application submits an action for verification before execution.
2. **Canonical hashing.** SafeGate normalizes the action request before computing a deterministic hash.
3. **Readiness.** Diagnostics and preflight report checks such as policy availability and registry status.
4. **Policy.** The verifier evaluates the action's risk level against the configured rules to determine whether approval is required.
5. **Review packet.** SafeGate records the action and its policy context for review.
6. **Approval packet.** The demo records a simulated decision, the canonical action hash and a configured approver ID. An authenticated approval requires evidence beyond these fields.
7. **Hardware attestation.** Verification of hardware-backed evidence is future work.
8. **Demo.** The runner explicitly requests simulation and records the results for matching, changed and denied actions.

## The Verification Loop

The `verifier` validates the action, computes its canonical hash and evaluates the policy. A policy that explicitly waives approval can allow the action. If the policy requires approval, the verifier checks the supplied packet against the action hash and the evaluated policy ID, rule ID and approval requirement. It also checks the packet's status and expiration, plus the named approver's active status and permitted method in the caller-configured registry.

Normal verification denies approval-required actions because today's packets carry no authenticated approval evidence. Only explicit demo verification can report a successful simulation. A matching demo result is for demonstration only. The `observe` module records the decision trace.
