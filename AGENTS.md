# AI contributor instructions

Keep the project independent from any individual AI tool or context-window size.

## Before writing code
1. Read `docs/MANIFEST.md` (invariants), `docs/ARCHITECTURE.md` (boundaries), the relevant `spec/` documents, and **only** the current stage task.
2. Inspect repository state and relevant tests. Never invent previously passing CI, executed benchmarks or hardware access.
3. Restate assumptions and list a narrow acceptance gate.

## Execution discipline
- Work on a feature branch. Never overwrite unrelated changes or merge to `main` without an explicit instruction.
- Make minimal, testable changes and preserve backward compatibility unless a migration is documented.
- Prefer a boring standard library prototype before introducing dependencies or custom VMs.
- Never use `eval`, `exec`, implicit dynamic imports or arbitrary device-address operations on descriptions.
- Treat unsigned or unauthenticated passports as untrusted. Do not call simulation a device driver.
- Put unresolved questions in the roadmap/decision log, not hidden assumptions.
- Limit task context: manifest + stage task + affected specs/files; avoid loading the entire repository.
- Report exactly what ran, what passed, what failed, and what was not tested.

## Completion checklist
A PR should explain goal, changed files, test command/output, failure cases, security limitations and remaining risks. Source, tests and documentation must agree.
