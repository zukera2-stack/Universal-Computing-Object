# Universal Computing Object (UCO)

**Status:** research architecture and experimental prototype — **not an operating system, certified driver framework, or production runtime**.

UCO explores a portable *logical computation object*: a versioned, machine-readable contract joining operations, state, capabilities, dependencies, identity references and execution constraints. Its implementation may be placed on a personal/home computing node or on competing remote providers without tying ownership to an operator.

**First falsifiable milestone:** run one immutable operation specification through two distinct, validated *simulated* device capability passports, obtaining equal verified results while generating distinct target adapters. No real GPU driver, firmware manipulation, arbitrary code execution or hardware discovery is part of Stage 01.

## Why this repository exists

Research questions:
- Can a small, shared trusted runtime replace duplicated infrastructure logic without imposing one massive kernel?
- Can device descriptions guide *deterministic specialization*, rather than generating unsafe, guessed drivers?
- Can state, data and authorized capabilities move across providers without transferring ownership or leaking protected information?
- Can semantic portability coexist with local execution, offline-first home nodes and competitive services?

See [manifest](docs/MANIFEST.md), [architecture](docs/ARCHITECTURE.md), [object contract](spec/UCO-OBJECT-v0.1.md), [device passport](spec/DEVICE-PASSPORT-v0.1.md), [roadmap](docs/ROADMAP.md), [Stage 01 task](tasks/STAGE01_TASK.md) and [AI workflow](AGENTS.md).

## Ground rules

1. A *logical* object is not a monolithic binary; source code, data, runtime and hardware adapters remain separable.
2. A portable bytecode or declarative graph is not automatically optimized native code.
3. Certification and signatures attest provenance and tested properties, **not universal correctness or freedom from bugs**.
4. Hardware-specific behavior requires documented or manufacturer-provided interfaces and may require proprietary firmware and compilers.
5. Open interoperability, user portability and local fallback are design goals, not current capabilities.
6. Invariants must become tests; claims must be backed by repeatable evidence.

## Scope now

Only documentation and an executable, standard-library prototype are targeted. Stage 01 deliberately uses simulated vector-processing devices; real devices, network migration, payment, licensing enforcement and encryption-at-compute remain out of scope.

## Contribution and license

No open-source license has been selected yet. Public source visibility alone does **not** grant permission to redistribute or modify it. An explicit license must be chosen by the repository owner before inviting external code contributions.

## Stage 01 prototype

From the repository root, using Python 3.11+:

```sh
python -m unittest discover -s tests -v
python -m uco_demo --object examples/vector_add.json --device examples/device_scalar.json --grant compute.vector.add.i32
python -m uco_demo --object examples/vector_add.json --device examples/device_chunked.json --grant compute.vector.add.i32
```

Expected result: `[5, 7, 9]` on both simulated targets. See [report](docs/STAGE01_REPORT.md) for verification status.
