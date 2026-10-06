# Analysis code — Koyama et al., *Science Immunology* (ady3001)

**IFN-γ-driven MHC class II expression by intestinal epithelial cells dictates
local cytolytic Th1 differentiation and intestinal stem cell loss**

Version 1.0.0 · 2026-09-21 · MIT licensed
Data: NCBI GEO **[GSE348009](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE348009)**

---

## What this is

The complete single-cell RNA-sequencing analysis code for the paper. It
regenerates **seven figures** — every scRNA-seq panel in the manuscript — from
the expression matrices deposited in GEO.

| Figure | Panels | Experiment | Script |
|---|---|---|---|
| **Fig 4** | B–D | Exp160, ileal IEC, naïve + 24 h TBI WT | `Exp160/01_fig4_figS6.R` |
| **Fig S6** | A–E | same | `Exp160/01_fig4_figS6.R` |
| **Fig S7** | B–E | Exp160, 24 h TBI WT + MHC-II KO | `Exp160/02_figS7.R` |
| **Fig S10** | A–D | Exp649, ileal ISC, day 7 post-BMT | `Exp649/01_figS10_qc.R` |
| **Fig 7** | B–F | Exp649, Lgr5+ ISC subset | `Exp649/02_fig7_figS11.R` |
| **Fig S11** | A–C | same | `Exp649/02_fig7_figS11.R` |
| **Fig S3** | A–C | Exp80, Marilyn T cells, ileal EL vs LP | `Exp80/02_figS3_from_deposit.R` |

(Panel A of Figures 4, 7 and S7 is an experimental schema, not data. Fig S3D–F
are flow cytometry and cytotoxicity assays, not sequencing.)

`FIGURE_MAP.tsv` lists all **124** output panels individually.

---

## Quick start

```bash
# 1. check the package itself (seconds; needs neither data nor R packages)
./verify_package.sh

# 2. build the R environment  (30-90 min from cold; needs a compiler)
export ADY3001_LIB=~/ady3001_Rlib
Rscript 03_environment/install_packages.R

# 3. download the supplementary files of GSE348009 into one directory, then
#    rearrange them into the per-cartridge layout the scripts expect
./tools/unpack_geo_download.sh ~/Downloads/GSE348009 ~/ady3001_data
export ADY3001_DATA=~/ady3001_data

# 4. choose where results go (default: ./ady3001_output in the current dir)
export ADY3001_OUT=~/ady3001_output

# 5. regenerate every panel
./run_all.sh
```

**Step 2 is required.** The scripts need Seurat **5.1.0** specifically, and a
stock or current R library will not do &mdash; Seurat 5.5.x and ggplot2 4.x both
break this code (see `03_environment/README.md`).
`install_packages.R` reads `r_packages.yml` and installs the recorded versions
into `$ADY3001_LIB` without touching your system library.

Results land in `$ADY3001_OUT` (default `./output`). Compare against
`EXPECTED_RESULTS.tsv` — those cell and cluster counts are exact, not
approximate.

### Step 2 is not optional

A GEO download is **flat**. The scripts expect one directory per cartridge, and
for Exp80 one directory per sample tag whose name **ends `_mm`**. Skipping the
unpack step makes a correct deposit look empty.

---

## Layout

```
01_original_code/      the Rmds as they were when the figures were made,
                       unmodified — including the two that were never published
                       to GitHub. READ KNOWN_ISSUES.md BEFORE RUNNING THESE.
02_figure_scripts/     the runnable transcription. This is what you execute.
   common/             config.R (paths) + load_bd.R (matrix loader)
   Exp160/ Exp649/ Exp80/
03_environment/        install_packages.R (use this), sessionInfo of the
                       verified runs, and lab_reference/ (the lab's own pin
                       scripts — deposited as a record, NOT runnable elsewhere)
04_bd_pipeline/        optional: FASTQ → matrices, version-pinned BD Rhapsody.
                       LAB-PATHED: these were written for this cluster and are
                       deposited for auditability, not turnkey re-execution.
05_verification/       path_rewrite.diff (the full diff proving the scripts are
                       path-only changes) plus the scripts that proved the
                       deposit reproduces the paper. Also lab-pathed.
tools/                 unpack_geo_download.sh
FIGURE_MAP.tsv         every panel → the script that writes it
EXPECTED_RESULTS.tsv   exact cell / cluster / panel counts
MANIFEST.sha256        checksums for every file here
```

---

## Environment

| | Exp160 / Exp649 | Exp80 |
|---|---|---|
| R | **4.4.0** | **4.3.2** |
| Seurat | **5.1.0** | **5.0.0** |

The two experiments used different Seurat versions; this is not a typo.

**Pin your library.** On 2026-09-18 the library these packages lived in was
updated in place, Seurat went 5.1.0 → 5.5.1 and ggplot2 3.4.4 → 4.0.3, and the
analysis stopped running the same day. `03_environment/install_r_pin.sh`
reinstalls the validated versions into a private library; `config.R` puts it
first on `.libPaths()`. See `03_environment/README.md`.

---

## Two corrections to the published Methods

Both were found by running the code, and both are documented with evidence in
`01_original_code/KNOWN_ISSUES.md` and `03_environment/README.md`.

1. **The mitochondrial threshold is 40 %, not 25 % — now corrected in both
   places.** The Methods previously said "`percent.mt` < 25 % (IEC analysis) or
   < 40 % (ISC analysis)"; they now read 40 % for both, and line 157 of
   `Exp160_Final.Rmd` was corrected to match on 2026-10-06. Every published
   object — including the IEC ones — has a `percent.mt` maximum of ~40.
   Filtering at 25 keeps 6,412 cells; the published Fig 4 object holds
   **8,032 cells in 7 clusters**, and the corrected Rmd reproduces it
   cell-for-cell — identical barcodes, identical cluster sizes, 100.00 %
   agreement, `percent.mt` max 39.9936 against the published 39.9936 (verified
   2026-10-06). The difference is material: the 1,620 additional cells have
   *higher* median complexity than the retained set and form a distinct cluster.

2. **The R version is 4.4.0, not 4.0.3.** The Statistical analysis section says
   "R (ver. 4.0.3) for RNAseq data". All five published Seurat objects record
   `SeuratObject` 5.0.2 internally, which requires R ≥ 4.1.0 and was released in
   May 2024. R 4.0.3 (October 2020) cannot load these objects.

---

## Reproducibility evidence

Every script here was run against a **clean room** containing nothing but the 28
processed files actually deposited in GEO, md5-verified against the upload
manifest, with no other project file reachable:

| Figure | Cells | Clusters | Cluster sizes | Cell-for-cell agreement with the published object |
|---|---|---|---|---|
| Fig 4 / S6 | 8,032 | 7 | identical | **100.00 %** |
| Fig S7 | 7,478 | 6 | identical | **100.00 %** |
| Fig S10 | 9,135 | 12 | identical | **100.00 %** |
| Fig 7 / S11 | 6,828 | 9 | identical | **100.00 %** |

Fig S3 reproduces by **two independent routes** — the four deposited per-tag
matrices, and the deposited Combined matrix split by the deposited
`Sample_Tag_Calls.csv` — which give byte-identical matrices; the dot-plot values
agree with the full eight-tag run to 4.4 × 10⁻¹⁶.

124 panels written, none empty.

### Known limits, stated plainly

- **UMAP orientation is not reproducible, and does not need to be.** A UMAP is
  defined only up to rotation and reflection. The Fig S3A rebuild is
  horizontally mirrored relative to the published panel; the structure,
  groupings and all quantitative values are identical.
- **Figures 7 / S11 do not reproduce from matrices regenerated from FASTQ.**
  They reproduce exactly from the deposited matrices, which is what GEO carries.
  Louvain clustering at resolution 0.5 sits near a community boundary for this
  dataset, so the 0.001 % molecule-level difference introduced by re-running the
  BD pipeline renumbers the map and yields 7 ISC communities instead of 9. The
  cell set is essentially unchanged (Jaccard 0.997). The script detects this and
  refuses to claim a reproduction rather than quietly subsetting the wrong
  cells.
- **Exp80's FASTQ→matrix step is not version-matched.** BD never published the
  v1.8 targeted CWL and it is not in the v1.8 container. The deposited matrices
  are BD's original output.
- **Do not add seeds.** Seurat's per-function seed defaults are already fixed and
  the original code never overrode them. Passing `set.seed(1234)` into
  `FindClusters` gives 8 communities where the published Fig 4 object has 7.

---

## Relationship to the GitHub repository in the Methods

The Methods cite `github.com/acyeh-lab/2024/tree/main/Koyama/scseq`. That
directory is **incomplete**: its `Exp160_Final.Rmd` is the pre-revision version
missing all of Figure S7 and Figure S6C, and the Exp80 code was never pushed at
all. **This archive supersedes it.**

---

## Citation

Please cite the article and this archive. See `CITATION.cff`.
