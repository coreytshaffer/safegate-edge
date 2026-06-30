# Release Notes

## safegate-sge-008 — End-to-End Demo Runner

SGE-008 adds a deterministic end-to-end SafeGate demo runner. The demo creates a human review packet, generates approved and denied approval packets, verifies the original action as allowed, verifies a mutated action as blocked with action_hash_mismatch, verifies a denied approval as blocked with approval_not_granted, exports a mutated-path evidence bundle, writes demo_summary.json, and generates a standalone README_DEMO.md for reviewer presentation.
