# UCO Manifest — stable principles (v0.1)

This is a concise architectural charter, **not** an implementation specification or claim of novelty.

## Purpose
Investigate whether computation can be represented as portable, verifiable, operator-neutral objects executed by a small trusted runtime and specialized using machine-readable descriptions.

## Invariants
- **User agency:** transport and ownership of object state do not depend on an individual cloud operator. Actual legal licenses and privacy policies remain explicit external contracts.
- **Portable meaning:** for supported deterministic operations, identical inputs under the same specified semantics produce identical output across conforming backends.
- **Least authority:** operations may access only capabilities explicitly granted to them. Device adapters receive scoped rights; no implicit kernel privileges.
- **Separate policy and mechanism:** a logical description can be unified while caching, scheduling, storage and CPU/GPU mechanisms remain specialized.
- **Described, not imagined, hardware:** no driver synthesis for unknown register-level behavior. Unsupported features fail closed.
- **Checkable changes:** versioned schemas, conformance vectors, reproducible builds, signed artifacts where applicable, and rollback of deployments.
- **Federation:** common interfaces with independent providers, exportable data and interoperable identities; no compulsory single operator.
- **Offline safety:** personal nodes maintain a defined minimum service when disconnected. SOS requires an independent communications/safety design.
- **Small trusted base:** minimize and audit the core instead of putting every driver, interpreter and service in one privileged kernel.

## Non-goals
A bug-free world; a universal free compute entitlement without funding; elimination of all human languages; arbitrary binary or live-GPU migration; replacing proprietary GPU firmware by a JSON file; replacing security review with AI-generated code.

## Design discipline
Normative details go under `spec/`; implementation and tests under `src/` and `tests/`; bounded tasks under `tasks/`. Every proposal names assumptions, threats, tests, failure cases, and measurable pass/fail criteria.
