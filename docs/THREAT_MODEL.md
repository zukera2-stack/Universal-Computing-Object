# Initial threat model — draft

## Trust boundaries
Untrusted user object JSON; untrusted device passport JSON; caller grants; trusted schema validator; plan selector; execution backend; future data store and provider federation.

## Candidate threats
- Schema confusion, type coercion and unsupported capability escalation.
- Passport identifies unsupported or unsafe device operations.
- Generated plans inject commands or obtain privileges outside the grant.
- Malicious input causes resource exhaustion or arithmetic overflow.
- Object state is tampered with or confused during migration.
- A cloud provider reads data or silently changes execution results.
- Licenses or identity credentials are forged or transferred without authority.
- A central orchestrator becomes a bottleneck or a single point of failure.

## Immediate mitigations (Stage 01)
Strict allowlist validation, resource bounds, checked arithmetic, no dynamic code execution, no device access, explicit grants, deterministic execution and differential testing.

## Future work
Content integrity and replay protection; signature chains, revocation and audit; encrypted storage and network; isolated execution and attestation; error budget and incident response; legal portability agreements; real DMA/IOMMU safety analysis.

**Important:** This is not yet a comprehensive security review.
