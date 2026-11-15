# Device passport v0.1 — exploratory draft

A *passport* is structured information about a **known** target's supported abstract operations and execution limits. Stage 01 passports refer to two simulated devices, not real hardware.

```json
{
  "schema_version": "uco.device.v0.1",
  "device_id": "sim-vector-a",
  "device_kind": "simulated",
  "interface_version": "uco.vector.v0.1",
  "operations": ["vector.add.i32"],
  "capabilities": ["compute.vector.add.i32"],
  "max_items": 1024,
  "strategy": "scalar"
}
```

A second simulated device uses `strategy: "chunked"` with identical documented semantics. Strategies are allowlisted; no executable code appears in a passport. The runtime specializes a plan deterministically according to the validated passport and operation. A passport does not provide a kernel driver, GPU ISA, firmware or a shader compiler.

## Later security additions
Device/vendor identification, signed manifests, revocation, trust roots, independently performed conformance tests, MMIO/DMA grant isolation, driver/firmware ABI versions, attestation policy and device-specific security advisories. A vendor signature proves provenance only under a trusted verification chain; certification requires a separate process.

## Validation rules for prototype
Reject unsupported schema/interface, unknown kind/strategy, missing operation or capability, nonpositive or excessive limits, and any unrecognized security-sensitive fields. A deterministic plan ID should be derived from canonical validated contract fields; never trust `device_id` as a security credential.
