# ADR-0004: Fail closed on untrusted-input resource bounds

- **Status:** Accepted
- **Date:** 2026-08-30

## Context

DataPR parses artifacts and opens profile files supplied by a pull-request workflow. A malformed or unexpectedly large input can consume memory, prolong analysis, or trigger an unhandled exception. Silently dropping the input would be worse because a reviewer could interpret missing evidence as safety.

## Decision

DataPR applies explicit manifest and profiling boundaries before expensive work and raises controlled domain errors when a boundary is exceeded. Manifest byte size is checked before reading; normalized nodes, columns, SQL length, and nested structure are validated. Profiling checks model count, file size, column count, and sample count, then configures a DuckDB memory limit and one execution thread.

The command fails with exit code 2 rather than producing a partial comparison. Default boundaries target pull-request review, and profiling limits can be raised explicitly for measured self-hosted environments.

## Consequences

- Resource exhaustion cannot silently become a passing report.
- Malformed artifacts produce concise user-facing errors instead of implementation exceptions.
- Very large legitimate projects may need explicit configuration or narrower generated samples.
- On-disk checks and DuckDB limits reduce risk but do not provide process isolation or a wall-clock deadline.
- Future timeout or subprocess isolation can extend this decision without changing the evidence schema.
