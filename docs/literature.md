# Literature and claim audit

Audit date: 2026-10-20. Sources are primary papers, original data and AAPM material.
There is no established single best score for arbitrary CORT objectives.

1. Craft et al. (2014), [CORT paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC4326207/),
   [data](https://doi.org/10.5524/100110). Full text and archive inspected. Confirms
   the five-angle phantom, Gy/MU units, voxel mapping, Table 2 controls, and Table 3
   LP formulation/results. Fixed-beam convex fluence optimization is established;
   beam selection and aperture restrictions introduce discrete/nonconvex choices.
   The paper explicitly limits aperture-dose accuracy available from these matrices.
2. AAPM, [TG119 instructions](https://www.aapm.org/pubs/tg119/TG119_Instructions_102109.pdf).
   C-shape easier-case dose-volume goals inform contextual metrics. This is not
   authorization to apply them to patients or a claim to reproduce commissioning.
3. O'Connor et al. (2017), [Fast non-coplanar beam orientation optimization based on
   group sparsity](https://arxiv.org/abs/1710.05308). Establishes that group-sparsity
   methods and accelerated proximal optimization for large angle sets predate this
   pilot. A new implementation alone is not novel. Abstract reviewed.
4. [Beam angle optimization for proton therapy via group-sparsity based angle
   generation](https://pmc.ncbi.nlm.nih.gov/articles/PMC10272076/) (2023).
   Exhaustive small-instance comparisons and angle replacement are relevant methods.
   Proton modality differs from this photon phantom; numerical gains do not transfer.
5. [Beam orientation optimization in IMRT using sparse mixed integer programming
   and non-convex fluence map optimization](https://pubmed.ncbi.nlm.nih.gov/40570902/)
   (2025). Recent mixed-integer/SOCP work shows this remains an active area.
   Abstract reviewed; exact methods and instances require full-text audit before
   claiming superiority to them.

User premises: original CORT matrices exist (confirmed); a manageable CPU case exists
(confirmed by file size and this pilot's execution); prescribed target coverage can
be balanced with healthy-structure dose (model supported, must be tested under each
frozen profile); genuine research improvement is accessible (unproven, assessed in
the contributor trial rather than assumed).

Settled limits: five-beam enumeration leaves no algorithmic plan-quality frontier
once every feasible LP is solved reliably. More CPU cannot improve a solved LP.
Larger angle sets, dose-volume feasibility and delivery decisions offer harder
problems, but require strong baselines and additional validation. Output scaling
is only a sensitivity model; CORT does not supply validated setup scenarios.
