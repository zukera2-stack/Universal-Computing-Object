# Stage 01 — Deterministic object specialization

**Objective:** falsify or demonstrate, at a small scale, the following claim:

> A single immutable, machine-readable operation contract can be validated and specialized against two distinct simulated device passports, producing equivalent deterministic results without changing the operation source.

## Scope
Python 3.11+ standard library only; no network, hardware access, package installs, driver probing, GPU dependencies, subprocess execution or code generation via `eval`/`exec`. No grand platform framework.

## Inputs
- A versioned object JSON (spec/UCO-OBJECT-v0.1.md).
- Two versioned simulated device passports (spec/DEVICE-PASSPORT-v0.1.md) differing in permitted implementation strategy (`scalar`, `chunked`).
- An explicit caller grant for `compute.vector.add.i32`.

## Implementation
1. Implement strict schema/field/type validation of objects, passports and grants. Reject unknown security-relevant fields and unsupported versions.
2. Implement a small deterministic specialization function producing an inspectable execution plan with strategy and stable plan hash.
3. Implement two separate implementations of `vector.add.i32` (scalar loop; chunk-based loop), both honoring checked signed 32-bit arithmetic and resource limits.
4. Make the object definition and input immutable from the runtime's perspective. Do not modify the object to select a target.
5. Provide a simple CLI: `python -m uco_demo --object examples/vector_add.json --device examples/device_scalar.json --grant compute.vector.add.i32`.
6. Provide positive and negative tests using `unittest`: same result, deterministic repeat, target specialization differs, missing grant, unsupported opcode, invalid schema, mismatched length, overflow, bool rejection, item limit, malicious/extra fields.
7. Provide `python -m unittest discover -s tests -v` command in README. Add CI for tests on Linux and Windows with an explicitly supported Python version.
8. Record example output, known limitations and whether acceptance criteria passed in `docs/STAGE01_REPORT.md`.

## Acceptance criteria
- Same UCO JSON used by both backends unmodified.
- Both backends return `[5, 7, 9]` for sample inputs.
- Plans differ by strategy; same validated contract inputs generate stable plan hashes.
- Invalid inputs and missing grants fail closed with useful errors.
- No arbitrary code execution; no device I/O or network calls.
- Tests run in CI. Explicitly disclose if CI or execution was not performed.

## Out of scope
Actual NVIDIA/AMD device support, shader compilers, firmware, signing infrastructure, license enforcement, real migration, end-to-end cryptography, generative driver synthesis, universal interpreter.

## Workflow
Develop on `prototype/stage-01-specialization`, leave `main` untouched, submit a PR; do not merge automatically. Changes should be scoped only to Stage 01 and justified by tests.
