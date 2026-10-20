# Radiotherapy optimization — Discovery@Home incubation pilot

Can fewer beam directions preserve target coverage while reducing dose to healthy
structures? This research-only pilot uses the original public CORT **synthetic
TG119 phantom**: five angles and 418 beamlets. It never connects to treatment
systems, imports clinical patient data, or produces treatment recommendations.

Douglas Colkitt is the maintainer. The pilot is hosted privately at
[discoveryathome/radiotherapy](https://github.com/discoveryathome/radiotherapy).
The public launcher remains paused; no hub submission is authorized. See [DISCOVERY.md](DISCOVERY.md),
[the planning specification](docs/planning-spec.md), and [AGENTS.md](AGENTS.md).

## Run

Python 3.14 with binary wheels is the tested environment (macOS arm64).
Other Python versions and operating systems have not been verified. No GPU, commercial solver, or MATLAB is needed. From this directory:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: -r requirements.lock
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m rtpilot.verify
.venv/bin/python -m rtpilot.verify_trial
.venv/bin/python -m unittest discover -s tests -v
```

The pinned raw matrices are included, so verification needs no data download.
`verify` independently recomputes every saved plan's full-grid dose and metrics.
It does not run the optimizer. To regenerate the experiments:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m rtpilot.run --out replay-results
MPLCONFIGDIR=.cache/matplotlib .venv/bin/python -m rtpilot.plot --results replay-results
```

Evaluate a new witness with `python -m rtpilot.evaluate PLAN.json --require-feasible`.
The candidate must reference the pinned data and planning-profile hashes. Compare
only within the same profile, beam budget and uncertainty model.

## What is established

Craft et al. provide an LP data-consistency baseline, not a recommended plan:
minimize mean Core + mean BODY dose, with target dose between 1 and 1.2 Gy and
Core dose at most 1.2 Gy. Their means are 0.2489 and 0.1021 Gy respectively.
This pilot checks the supplied original solution and re-solves the same LP.
[Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC4326207/),
[data DOI](https://doi.org/10.5524/100110).

Fixed-beam convex fluence optimization is established. The research opportunity is
in discrete beam selection, delivery restrictions, and validated uncertainty models.
The five-angle case is small enough to enumerate; improvements over a weak heuristic
are not new state-of-the-art results. See [literature](docs/literature.md).

## Outputs

- `results/comparison.json` and `.csv`: candidate metrics, failures and solver diagnostics.
- `results/plans/`: complete fluence witnesses, with hashes and beam budgets.
- `results/dvh.png`, `dose_maps.png`, `beam_tradeoff.png`: independently recomputed figures.
- `docs/report.md`: results, limitations, and launch-readiness assessment.
- `trial/`: timed contributor trial and evidence, when completed.

A feasible matrix plan is **not** evidence of clinical safety or machine
 deliverability. The evaluator is independent software using the same physical
influence matrices; it is not a second dose engine or independent-human review.
Beam-count and fluence limits are delivery proxies, without MLC sequencing,
scatter recalculation, collision checking, or measurement-based QA.

Code: MIT. Authored documentation: CC BY 4.0. CORT data: CC0 with attribution to
Craft, Bangert, Long, Papp and Unkelbach (2014). See `LICENSE` and `data/README.md`.

The fixed 30-minute contributor trial found a feasible 10-MU-grid improvement; see
[the assessment](docs/report.md) and [progress chart](results/contributor_progress.png).
The original three-beam task is numerically infeasible. This exact benchmark is
recommended for incubation, not an inaugural featured launch.
