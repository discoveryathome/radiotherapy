# Public demo: can we protect the center while covering the C-shape?

The picture is a synthetic test phantom, not a person's scan. A C-shaped target
wraps around a central structure we want to spare. Each available beam direction
contains many small beamlets whose intensities can be adjusted.

The computer must satisfy two demands at once: enough dose throughout the target,
and limited dose elsewhere. Simply turning every beam down fails the target test.
A lower healthy-dose score only counts if all the frozen constraints still pass.

Show the dose maps using a common color scale, then show the dose-volume curves:
“On this curve, a higher target dose means better coverage up to the allowed ceiling;
for the central structure, lower dose is preferable.” The evaluator computes these
curves directly from the saved beamlet settings and the original data.

The strongest result of this initial pilot is a trustworthy, reproducible comparison,
not a newly discovered cancer treatment. With these five available directions and
our frozen limits, three directions are insufficient. Four and five can meet the
research envelope, but the initial plans fail stricter reference dose-volume goals.
This is a useful scientific finding about this particular benchmark; it says nothing
about what a person should receive in a clinic.

A future contributor demo should show an actual accepted before/after result under
the same constraints, alongside its gap to a strong baseline. Do not present an
infeasible low-score plan as an improvement, or label a known LP result as a discovery.
The current tiny beam-selection case is largely exhaustible; a featured project
needs a validated harder discrete challenge before promising continuing progress.
