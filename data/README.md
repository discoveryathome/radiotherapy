# Pinned CORT TG119 source data

Original dataset: Craft D, Bangert M, Long T, Papp D, Unkelbach J (2014),
Supporting material for "Shared data for IMRT optimization research: the CORT dataset".
DOI: https://doi.org/10.5524/100110
Paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC4326207/

`manifest.json` pins SHA-256 hashes for the original archive and every used file.
Downloaded 2026-10-20 from the archive URL recorded there. Files are original bytes,
not a substituted matRad-generated influence matrix. Only the synthetic phantom is
used. The large CERR object and separate DICOM archive are unnecessary and omitted.

Dose is Gy/MU; source voxel lists are 1-based. AP changes fastest, LR next and SI
slowest; array shape is (167,167,129) in Fortran order. Beam order is
0,72,144,216,288 degrees with 98,70,90,90,70 beamlets respectively.
The five supplied `beamletSol` files are the authors' LP witness.

GigaDB terms and the paper's data waiver specify CC0 unless otherwise stated:
https://gigadb.org/term . Credit the authors and DOI in derived work.
No additional data license was found in the archive.
