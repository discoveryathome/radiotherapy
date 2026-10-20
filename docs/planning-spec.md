# Frozen planning specification v1

The machine-readable files in `config/` were committed before new optimization.
Do not change them to make a candidate win. An altered objective is a separate
benchmark version; sensitivity experiments do not replace the primary score.

## Exact reproduction

`paper.json` reproduces CORT Table 3 at its original 1 Gy scale. Minimize
mean(Core) + mean(BODY), with every OuterTarget voxel in [1,1.2] Gy, every Core
voxel at most 1.2 Gy, and nonnegative fluence. BODY includes target and Core,
matching the original paper. No upper fluence bound is added.

## Primary research benchmark

`research.json` scales the published voxel-dose envelope to a **synthetic 50 Gy
prescription** and adds explicitly chosen research limits:

| Quantity | Frozen requirement |
|---|---|
| Every target voxel | 50–60 Gy |
| Every Core voxel | At most 60 Gy |
| Core mean | At most 20 Gy |
| Healthy-body mean | At most 10 Gy |
| Each beamlet fluence | 0–5,000 MU |
| Sum of beamlet fluences | At most 400,000 MU |
| Allowed active angles | Primary 3; separate comparisons at budgets 1–5 |
| Objective | Minimize Core mean + healthy-body mean, in Gy |
| Dose feasibility tolerance | 0.0001 Gy |
| Fluence feasibility tolerance | 0.00001 MU |
| Active beam | Any beamlet magnitude above 0.000001 MU |

HealthyBody = BODY minus the union of OuterTarget and Core. All voxels in each
structure are evaluated; none are sampled or withheld from the constraints.
Voxel volume is constant: 0.300616 × 0.300616 × 0.25 cm³. No fractional-volume
correction is inferred. Negative fluence, nonfinite numbers, mismatched hashes,
and incorrect dimensions are rejected. Feasibility precedes objective ranking.
No candidate is normalized after optimization without being evaluated again.

These constraints are an explicit research test case, **not clinical acceptance
criteria**. The relatively loose 120% target ceiling permits comparison with the
published baseline. The Core and healthy-body mean caps and fluence caps are
pilot design choices, not limits established by a clinical authority. The sum of
beamlet MU is an optimization proxy, not total machine MU or treatment time.

For context, report separately the TG119 easier C-shape goals: target D95 ≥50 Gy,
target D10 ≤55 Gy, and Core D5 ≤25 Gy. The original instructions prescribe nine
fields, unlike CORT's five. A research-feasible plan may fail these goals. Passing
the three metrics still does not constitute commissioning or clinical validation.
[Source](https://www.aapm.org/pubs/tg119/TG119_Instructions_102109.pdf).

## Metrics and numerical checks

D(p) is the empirical upper-tail order statistic: sort n doses ascending and take
index n−ceil(p*n/100). Thus at least p% of voxels receive D(p) or more. V(q) is
the percentage of voxels receiving at least q% of prescription, using literal
threshold comparisons without an implicit normalization. Numerical boundary values
can slightly affect V100; voxel residuals use the stated dose tolerance.

Report target D98/D95/D50/D10/D5/D2, V95/V100/V110/V120, minimum/maximum/mean;
the same statistics for Core, BODY and HealthyBody; all constraint residuals;
beam count; objective; maximum fluence and beamlet-sum fluence.

Optimizer dose uses a concatenated CSR sparse matrix-vector product. The evaluator
loads original MAT matrices independently and sums individual CSC columns in reverse
order using extended precision where available. The difference must be ≤1e−9 Gy.
Both calculations use CORT's QIB pencil-beam model. Neither independently validates
transport physics, patient motion, scatter, absolute calibration, or delivery.

## Sensitivity and comparison rules

Predeclared output gains: 0.98, 1.00, 1.02. Robust candidates enforce all dose
constraints at both endpoint gains; this covers intermediate positive global gains
by monotonicity. These synthetic global-gain scenarios are not geometric setup or
anatomical uncertainty. No robustness generalization is claimed.

Round beamlet intensities to 1 and 10 MU; do not repair or rescale silently.
Re-optimize at Core objective weights 0.5 and 2.0, but evaluate and report using
the primary weights as well. Re-solve the best nominal three-angle subset with
HiGHS IPM and tighter tolerances. Record numerical dual residuals and gaps; these
are floating-point diagnostics, not formal certificates.

Enumeration covers all 31 nonempty subsets of the five available angles. Each
successful subproblem is a convex LP. A time limit or numerical failure must remain
unresolved; it must not be described as infeasible or as a completed optimality proof.
A backward greedy baseline uses the same subproblem solver, starting from five
beams and removing the angle with the least objective cost at each step.
