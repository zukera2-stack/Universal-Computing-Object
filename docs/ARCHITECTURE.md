# Architecture sketch (hypothesis)

```text
phones / watches / glasses / thin terminals
                   |
       home node (offline-capable)
                   |
          open federation API
           /             \
     provider A        provider B

logical UCO envelope: identity / operation / data refs / state / grants / constraints
                  |
      schema validator + policy gate
                  |
        deterministic planner
             /           \
    simulated device A   simulated device B
             \           /
        result checker (Stage 01)
```

## Boundaries
1. **Object envelope:** versioned semantics and integrity metadata; data references are separate from large blobs.
2. **Authorization:** authenticated identity, capability grants, revocation and policy; do not mistake metadata for enforceable access controls.
3. **Runtime:** validation, scheduling and accounting. A capability-scoped adapter runs outside the privileged core where the platform permits.
4. **Device passport:** a signed *claim* describing a known interface, supported operations, limits and producer. Signature verification, trust roots and conformance certification are separate processes.
5. **Persistence:** migration uses durable snapshots or negotiated checkpoint protocols. State conversion requires schema versions; distributed transactions, open sockets and external side effects need separate treatment.
6. **Provider federation:** portability of data formats, identity references and service obligations; licensing rights cannot be assumed transferable merely because a file moves.
7. **Execution backend:** interpreter/JIT/AOT, accelerator compiler or software fallback as appropriate. Hardware drivers remain specific where necessary.

## Why no single unified cache
CPU cache coherence, VM page replacement, DB buffer managers and cloud archival have different latency and consistency guarantees. Reusable *intent* and hints may be shared, but one central cache manager is not presumed better or safer. Benchmark before consolidating.

## Security baseline
- Untrusted device descriptions never directly grant MMIO, DMA or kernel execution rights.
- Verify signatures against independently managed trust roots; distinguish signed from certified.
- Enforce IOMMU and process isolation for real-device deployments (out of scope now).
- Treat device capabilities as an allowlist; reject ambiguity, version mismatch and unknown opcodes.
- Stage 01 does not evaluate arbitrary text as code or load third-party plugins.
- Hostile inputs and deterministic replay must be part of conformance tests.

## Engineering risks
Cross-architecture floating-point differences, timing and real-time constraints, private firmware, data gravity, bandwidth and latency, centralization risks, economics of a universal free service, legal license transfer, trusted execution limitations, hidden workload-specific optimizations.

## Stage 01 boundary
A **simulator** is not a driver. It proves only that one abstract operation contract can be interpreted by two different capability descriptions with equal semantics. It does not prove automatic support for GPUs.
