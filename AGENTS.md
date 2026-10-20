# Agent entry

Read DISCOVERY.md, docs/planning-spec.md and docs/report.md before proposing work.
This is research on a synthetic phantom only. Do not connect to clinical systems,
import patient data, export treatment instructions, or infer clinical safety.

Run the source-control check and reject-invalid tests first. Preserve the pinned
matrices, voxel mapping, profile hashes and evaluation code. Candidate work must
not change the evaluator to pass. A profile change requires a new benchmark version
and maintainer review. Independent verification is cheap; full enumeration is slower.

The maintainer authorized private hosting at discoveryathome/radiotherapy. No hub
PR or external messages are authorized. Record evidence and a fenced discover JSON handoff. Douglas Colkitt maintains the proposal; review
capacity and public launch approval are not yet declared. Do not claim novelty from
fixed-beam convex optimization or from beating a deliberately weak baseline.
