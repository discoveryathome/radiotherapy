# Same-agent, 30-minute contributor trial

The fixed trial interval is 2026-10-20 20:18–20:48 UTC. `protocol.json` was frozen at
the start; `base-commit.txt` identifies the starting code. This is a bounded technical
trial by the setup agent, not an independent or blind onboarding study. Setup and
final packaging outside this window must not be counted as contributor progress.

The contributor may change optimization methods but not data, primary constraints,
objective, or evaluator. Extra dose-volume goals are the separately reported TG119
reference criteria already present in the frozen profile. Secondary feasibility
search does not redefine the primary leaderboard.

`events.jsonl` records milestones. `initial-comparison.json` preserves the initial
exhaustive experiment. `dvh/` contains strict voxel-exemption experiments; `repair/`
contains attempts that minimize an explicitly reported relaxation of extra DVH caps.
A positive relaxation is a failure to meet the extra goals, not an accepted plan.
Full independent dose and primary metrics are retained for feasible iterates.

Machine: Mac14,2, 8 logical CPUs, 24 GiB RAM. Load average around 58 was observed
while many unrelated workloads ran. Wall timings are not clean CPU benchmarks;
per-solve CPU seconds where available are more informative. No speedup claim is
supported without interleaved controlled runs on an otherwise idle machine.
