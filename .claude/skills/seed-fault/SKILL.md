---
name: seed-fault
description: Introduce a controlled temporary fault, evaluate test coverage, and verify the repair.
---

# Seed Fault

Use this skill to evaluate whether the repository's
tests and hooks detect a methodological error.

## Workflow

1. Use $ARGUMENTS as the requested fault. If empty or unclear, ask the user which fault to introduce.
2. Check git status and identify the affected files.
   Preserve all unrelated user changes.
3. Run make test to establish a clean baseline.
4. Introduce exactly one temporary fault.
5. Observe the hook output and record any failing tests.
6. If the fault is not detected, explain the coverage
   gap and propose a regression test.
7. Restore the original implementation.
8. Run make test and verify that all tests pass.
9. Append the findings to docs/SEEDED_FAULTS.md.

## Required documentation

- File and exact change introduced.
- Expected failure and actual hook output.
- Whether the existing tests detected the fault.
- Number of agent turns required for repair.
- Any additional regression test needed.

## Constraints

- Never modify the original raw dataset.
- Never tune models using the test set.
- Never overwrite reports/metrics.json.
- Never commit intentionally faulty code.
- Never fabricate test results or hook output.
- Obtain user approval before adding regression tests.
- Do not claim completion until the repair is verified.
