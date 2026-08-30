# v1 stability policy

DataPR separates software-version readiness from production-adoption evidence.
Version 1.0 will mean that the documented interfaces are stable, tested, and
supported. It will not claim that every SQL construct, warehouse, or operating
environment has been validated by independent production users.

## Public contract

The v1 compatibility boundary includes:

- the `doctor`, `compare`, and `measure` command names, documented arguments, and
  exit-code meanings;
- configuration version 1, described by
  [`config-v1.schema.json`](../schemas/config-v1.schema.json);
- comparison result schema 1 and measurement schema 1;
- documented finding IDs, decision values, severities, confidence, provenance,
  and coverage semantics;
- GitHub Action input and output names; and
- the executable contract `datapr --version`.

The machine-readable [`public-v1.json`](../contracts/public-v1.json) snapshot is
checked on every supported Python version. Additive evolution is allowed; removal
of a declared element fails the contract suite.

Python modules under `datapr` are implementation details unless this document or
the API reference explicitly names them. SQL parser behavior is capability-backed,
not a promise to accept every construct in a named dialect.

## Compatibility rules

During v0.5 and the v1 release-candidate period, maintainers avoid intentional
breaking changes to the public contract. Starting with v1.0:

- compatible minor releases may add optional fields, findings, commands, and
  arguments;
- consumers of JSON contracts must ignore unknown fields;
- existing field meanings, command names, Action inputs, and configuration keys
  do not change within v1;
- a planned removal must be documented and deprecated for at least one minor
  release before the next major version; and
- security fixes may disable unsafe behavior immediately, with the exception and
  migration path documented in the release notes.

The latest v1 minor release and the immediately preceding v1 minor release receive
compatibility fixes. Security reports are assessed for every supported v1 release;
maintainers may require upgrading to the newest patch.

## Exit codes

| Command | Code | Meaning |
| --- | ---: | --- |
| `doctor` | 0 | Manifest is readable and supported. |
| `compare` | 0 | Analysis completed and enforcement did not block. |
| `compare --enforce` | 1 | Analysis completed and policy decided `fail`. |
| any command | 2 | Configuration, input, manifest, Git, or profiling error. |

`measure` reports the policy decision in JSON but returns 0 after successful
measurement generation.

## Engineering gates for v1.0

The v1.0 release is eligible when all of these are true:

- the public contract is documented and regression-tested;
- source distribution and wheel build, install, and execute cleanly;
- Python 3.10–3.12, composite Action, dialect corpus, synthetic acceptance matrix,
  golden contracts, resource limits, and release verification pass on protected
  `main`;
- v1 release and rollback procedures have been rehearsed with an immutable tag;
- security, support, upgrade, and known-limitation documentation is current; and
- no unresolved critical correctness or security issue is known.

Independent adoption, precision, and time-to-first-report remain important product
signals, but they are tracked after release under a separate production-evidence
status. They do not block a truthful v1.0 engineering release.
