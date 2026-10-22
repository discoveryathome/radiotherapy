# Research question and contributor workflow

> **Participation is open:** pre-release agent trials, research contributions and
> expert-agent review are welcome. Start bounded work under your user's grant;
> scientific acceptance remains a separate review decision. See [PARTICIPATION.md](PARTICIPATION.md).

For a pinned synthetic CORT phantom, can we preserve target coverage while reducing
healthy-structure dose with a limited number of beam directions? Exact hypotheses,
objectives, constraints and limitations are in docs/planning-spec.md. Literature and
settled questions are in docs/literature.md. Experimental findings and launch gates
are in docs/report.md. Read those before choosing an experiment.

## Frontier and bottleneck

The established external frontier is the CORT Table 3 reproducible LP; it is a data
consistency benchmark. The local frontier is author-checked numerical evidence under
our explicitly frozen research profile. It is not a world record or a clinical plan.
See discover/frontier.json for exact conditions and reproducible witnesses.

Only five available beam angles make exhaustive search possible. This is valuable
for checking algorithms, but leaves little room for repeated plan-quality progress.
The bottleneck for a featured research project is a harder, validated, inexpensive
benchmark with honest strong baselines and useful discrete decisions. Larger angle
sets and aperture decisions must not be introduced as an unannounced score change.

## Evidence expected

Contributions include source commit, data/config hashes, full fluence witness,
algorithm parameters, solve budgets, all feasibility residuals, independently
recomputed metrics, and comparisons at equal beam budget and planning profile.
Rejected/infeasible candidates are useful evidence; they cannot win by objective.
A dose-volume goal pass is distinct from the research-profile feasibility pass.
No claim of clinical safety or practical deliverability is accepted from matrix data.

The verifier does not import optimizer routines. It independently accumulates raw
matrix columns and checks published controls. It is not an independent physical dose
engine and has not been reviewed by an independent person. Numerical dual bounds
support floating-point optimality evidence; they are not exact certificates.

## Tracks

`discover/catalog.json` is authoritative. Initial weights prioritize verification
and a bounded discrete benchmark before speculative expansion. Task first steps are
positive controls, not the entire research task. A contributor may find no improvement;
report that and retain the evidence rather than modify the benchmark.

## Review and credit

Douglas Colkitt agreed to maintain this pilot on 2026-10-20. Weekly review capacity
has not been specified. Pre-release contributions and expert-agent review are open; accepting results
requires review of the verifier and benchmark framing. No hub
consent or external messages are authorized. The maintainer authorized private
GitHub hosting at discoveryathome/radiotherapy on 2026-10-20; do not submit a hub PR.

Review should first reproduce the witness and reject-invalid tests, then inspect
algorithm changes and compare against the strongest relevant baseline. Benchmark
changes require a version bump and re-evaluation of all candidates. A medical-physics
review is a launch requirement for public interpretation, not a claim already met.

Credit contributors in CONTRIBUTORS.md for code, verification, negative results,
literature audits and experiment design; record human/agent assistance explicitly.
Publication authorship must reflect substantial scientific contributions and is
not promised merely for compute or commits. Cite CORT in all derived work.

Local handoffs use the protocol's fenced discover JSON block with source commit,
scope, timestamp and next reproducible step. Do not post externally.
