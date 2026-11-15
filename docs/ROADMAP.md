# Roadmap — bounded, test-first research

| Stage | Question | Deliverable | Gate |
| --- | --- | --- | --- |
| 00 | What is actually claimed? | Manifest, architecture, draft schemas, threats | Review scope and falsifiable hypotheses |
| 01 | Can one object specialize into two conforming adapters? | Standard-library simulator and test vectors | Both targets return same values; negative tests pass |
| 02 | Can shared policy choose storage without breaking semantics? | Hot/warm/cold simulation with benchmark | Correctness preserved, measured costs vs baseline |
| 03 | Can state safely move between home node and two providers? | Local-process checkpoint and resume | Versioned snapshots and rollback tests |
| 04 | Can scoped peripheral objects remain isolated? | Mock userspace device service | Fault injection, privilege checks |
| 05 | Can two independent implementations interoperate? | Public conformance suite and two runtimes | Cross-implementation validation |
| 06 | Are real hardware paths feasible? | Vendor-interface survey / security review | Explicit feasibility decision, no assumed GPU driver magic |

Every stage is optional until the prior gate has evidence. No production claim follows from a simulator.

## Decision log
- D-001: UCO is a logical unit, not necessarily a single binary.
- D-002: Operator federation, no single mandatory provider.
- D-003: Standardize semantic contracts; backends may use different runtime technologies.
- D-004: Hardware passports select known strategies; no arbitrary generated code.
- D-005: Stage 01 uses two simulated devices, one operation and no privileged I/O.
- D-006: Main branch changes should be reviewed through a PR for the initial foundation.
