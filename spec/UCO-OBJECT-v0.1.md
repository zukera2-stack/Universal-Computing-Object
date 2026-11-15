# UCO object contract v0.1 — exploratory draft

Stage 01 uses canonical JSON with the following conceptual fields:

```json
{
  "schema_version": "uco.object.v0.1",
  "object_id": "vector-add-example",
  "operation": {"opcode": "vector.add.i32", "semantics": "checked-int32"},
  "inputs": {"a": [1, 2, 3], "b": [4, 5, 6]},
  "requirements": {"max_items": 3, "deterministic": true},
  "requested_capabilities": ["compute.vector.add.i32"]
}
```

Semantics: pairwise integer addition; reject nonintegers (including Booleans), unequal vectors, overflow outside signed 32-bit range, unsupported schema/opcode/capability, and size limits. No implicit truncation or numeric promotion. The caller must separately authorize the requested capability before execution. Stage 01 runs no untrusted executable bytecode.

## Beyond Stage 01 (non-normative)
A future object may reference an operation DAG or validated bytecode, typed immutable content-addressed blobs, checkpointable state, dependency hashes, resource budgets, security policies, identity claims and license *references*. A license reference is not itself legal authorization. Version negotiation and validation will precede any executing implementation.

## Properties to test
Determinism, input isolation, compatible-result equivalence, capability rejection, schema rejection, integer overflow handling, reproducible adapter identity and negative tests. Stage 01 may deliberately support only one opcode.
