# SafeGate Edge

SafeGate Edge is a local approval gateway for AI agents and automation workflows. It blocks high-risk actions until a human physically approves the exact action, then creates verifiable evidence showing what was requested, what was approved, what changed, and whether execution was allowed or blocked.

> **MFA verifies identity. SafeGate verifies the action.**

## The Hash Contract

The heart of SafeGate Edge is the **canonical action hash**. Before an action can be approved, it must be hashed. This ensures that the approval is cryptographically bound to the *exact* action requested. If the action is mutated in any way after approval, the hash changes, and the gateway will block the action.

### Included Fields

An `ActionRequest` must include the following fields, all of which are included in the hash:
- `action_id`: Unique identifier for the action.
- `action_type`: Category of the action (e.g. "delete_customer_exports").
- `requester`: Identity of the agent or process requesting the action.
- `command`: The exact command or function to be executed.
- `target`: The target resource (file path, DB record, etc.).
- `working_directory`: The directory in which the command will run.
- `risk_level`: The risk classification (e.g. "high").
- `created_at`: ISO 8601 timestamp of when the request was made.
- `expires_at`: ISO 8601 timestamp of when the request expires.
- `metadata`: Additional context, provided as a nested dictionary.

### Canonicalization Algorithm

To ensure deterministic hashing across different platforms and programming languages, the `ActionRequest` JSON object is canonicalized before hashing using the following rules:

1. **Sort Keys**: All keys in the JSON object (and any nested objects) are sorted lexicographically.
2. **Stable Separators**: No whitespace is allowed around separators. The compact form `","` and `":"` is strictly used.
3. **UTF-8 Encoding**: The JSON string is encoded to UTF-8 without escaping non-ASCII characters (`ensure_ascii=False`).

The resulting byte string is then hashed using SHA-256, and prefixed with `sha256:` to produce the final digest (e.g., `sha256:abcd...`).

## Usage & Demo

The SafeGate CLI allows you to compute hashes and verify approvals.

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