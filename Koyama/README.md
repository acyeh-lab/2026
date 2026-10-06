# Koyama *et al.*, *Science Immunology* — single-cell RNA-seq analysis code

Analysis code for:

> **IFN-γ-driven MHC class II expression by intestinal epithelial cells dictates
> local cytolytic Th1 differentiation and intestinal stem cell loss**
> Koyama M, Yeh AC, … Hill GR. *Science Immunology*

| | |
|---|---|
| **Data** | NCBI GEO [GSE348009](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE348009) |
| **Code archive** | Zenodo DOI `<concept DOI — to be added>` |
| **Platform** | BD Rhapsody WTA + AbSeq (Exp160, Exp649); BD Rhapsody targeted panel (Exp80) |

Everything here regenerates from the **processed expression matrices deposited
in GEO**. Three independent single-cell experiments comprise seven figures in the paper, one subfolder for each experiment.

---

## The original R Markdown files, and the figures they generate

These are the analysis notebooks as actually run. Three of them produce every
scRNA-seq figure in the paper.

| R Markdown | Author | Lines / chunks | Generates | Experiment |
|---|---|---|---|---|
| `Exp160/Exp160_Final.Rmd` | A. Yeh | 1,551 / 17 | **Fig 4B–D**, **Fig S6A–E**, **Fig S7B–E** | Exp160 |
| `Exp649/Exp649_Final.Rmd` | A. Yeh | 829 / 10 | **Fig 7B–F**, **Fig S10A–D**, **Fig S11A–C** | Exp649 |
| `Exp80/241221_Marilyn.Rmd` | S. Furlan | 155 / 6 | **Fig S3A–C** | Exp80 |

Two earlier working notebooks are included as the historical record. Neither
produces a figure the three above do not:

| R Markdown | Lines / chunks | What it is |
|---|---|---|
| `Exp160/Exp160_AYEH_241108_FINAL.Rmd` | 489 / 7 | The 2024-11-08 ancestor of `Exp160_Final.Rmd`. Fig 4 / S6 only — pre-dates the Fig S7 revision. |
| `Exp649/Exp649_AYEH_241104_FINAL.Rmd` | 3,200 / 59 | The full working notebook. Contains `Exp649_Final.Rmd`'s 10 chunks as chunks 1–10, plus 49 of exploratory analysis. |

> **The `_FINAL` suffix means opposite things in the two pairs**, which is the
> most confusing thing about this directory. For **Exp160**, `Exp160_Final.Rmd`
> is the *newer, larger* file and `…_AYEH_241108_FINAL.Rmd` is its ancestor. For
> **Exp649** it is reversed: `…_AYEH_241104_FINAL.Rmd` is the big working
> notebook and `Exp649_Final.Rmd` is the trimmed version. Go by the chunk
> counts above, not the filenames.

### Read this before running any `.Rmd`

They are deposited as the **historical record** and **will not knit from a clean
session** — see `KNOWN_ISSUES.md`. In short: `order_cells()` blocks on an
interactive prompt, `test0_1` is never assigned, and `saveRDS` writes straight
into the analysis directory, so knitting in place overwrites published objects.
**Use the `.R` scripts to execute anything.**

---

## The executable scripts, and the figures they generate

Transcribed from the notebooks above, path-parameterised, and verified to
reproduce the published objects cell-for-cell.

| Manuscript figure | Panels | Script | Experiment |
|---|---|---|---|
| **Fig 4B–D** | 22 | `Exp160/01_fig4_figS6.R` | Exp160 |
| **Fig S6A–E** | 17 | `Exp160/01_fig4_figS6.R` | Exp160 |
| **Fig S7B–E** | 26 | `Exp160/02_figS7.R` | Exp160 |
| **Fig S10A–D** | 7 | `Exp649/01_figS10_qc.R` | Exp649 |
| **Fig 7B–F + Fig S11A–C** | 39 | `Exp649/02_fig7_figS11.R` | Exp649 |
| **Fig S3A–C** | 5 | `Exp80/02_figS3_from_deposit.R` | Exp80 |

**124 panels total** (122 PDF + 2 PNG); 8 are QC plots, not manuscript panels.

Fig 7 and Fig S11 are one row because they cannot be separated: 11 panels are
Fig 7 only, 10 are Fig S11 only, and **18 are labelled as spanning both**. Any
split would be invented. Likewise `01_fig4_figS6.R` produces Fig 4 and Fig S6
from a single clustering, and cannot be split without re-clustering.

### Run order

```
Exp160:  01_fig4_figS6.R   and   02_figS7.R        independent
Exp649:  01_figS10_qc.R   ──►   02_fig7_figS11.R   SEQUENTIAL
Exp80:   02_figS3_from_deposit.R                   standalone
```

`Exp649/02_fig7_figS11.R` does **not** read the matrices — it reads
`all_cells_processed.RDS` written by `01_figS10_qc.R`.

---

## Which processed file each script reads

| Script | Reads | GEO sample |
|---|---|---|
| `Exp160/01_fig4_figS6.R` | `cartridge1_RSEC_MolsPerCell.csv`, `cartridge2_RSEC_MolsPerCell.csv` | GSM10065191, GSM10065192 |
| `Exp160/02_figS7.R` | `cartridge2_RSEC_MolsPerCell.csv`, `cartridge3_RSEC_MolsPerCell.csv` | GSM10065192, GSM10065193 |
| `Exp649/01_figS10_qc.R` | `Cart1_RSEC_MolsPerCell.csv`, `Cart2_RSEC_MolsPerCell.csv` | GSM10065194, GSM10065195 |
| `Exp649/02_fig7_figS11.R` | `all_cells_processed.RDS` (from script 1) | — |
| `Exp80/02_figS3_from_deposit.R` | the four `*_SampleTag0{5,6,7,8}_mm_RSEC_MolsPerCell.csv` | GSM10065196 |

`cartridge2` is read by **both** Exp160 scripts and re-clustered separately in
each — that is intentional, not duplication.

**RSEC, not DBEC.** WTA Rhapsody applies RSEC only; the `_DBEC_` files are
deposited for completeness and read by nothing here. Exp80 is a *targeted*
panel, where DBEC would be meaningful — but the published analysis read RSEC, so
RSEC is what these scripts use.

---

## Version manifests

One YAML per experiment. Each is **generated** by parsing the recorded
`sessionInfo`, not typed by hand, and the generator fails if the R environment
is inconsistent or a package appears at two versions.

| File | R / Seurat | BD pipeline | Contents |
|---|---|---|---|
| `Exp160/Exp160_versions.yaml` | 4.4.0 / 5.1.0 | **1.9.1** | 2 scripts, 177 indirect packages, 9 inputs with md5 |
| `Exp649/Exp649_versions.yaml` | 4.4.0 / 5.1.0 | **1.10.1** | 2 scripts, 137 indirect packages, 8 inputs with md5 |
| `Exp80/Exp80_versions.yaml` | **two environments** | **1.8** | 11 inputs with md5, 7 caveats |
| `r_packages.yml` | — | — | all 195 R packages at recorded versions, for install |
| `environment.yml` | — | — | the conda environment |

Each carries `environments:` (R version, platform, BLAS, attached packages per
script, and the indirect `namespace:` set — `fgsea`, `Matrix` and `presto` all
affect numbers), `bd_rhapsody:`, `reads:`, `inputs:` with sizes and md5,
`expected_results:` with exact cell and cluster counts, and `caveats:`.

**Exp80 has two environment blocks, deliberately.** `original_2024` is
R 4.3.2 / Seurat 5.0.0 on macOS — recovered from the rendered
`241221_Marilyn.html`, and the **only original `sessionInfo` that exists for any
published analysis in this paper**. `deposit_rerun` is R 4.4.0 / Seurat 5.1.0 on
Linux. They differ, which makes the Fig S3 reproduction a deliberate
version-*drift* test rather than a version-matched run.

---

## Layout

```
Koyama/
  README.md                     this file
  r_packages.yml                all 195 packages, for install
  environment.yml               conda environment
  common/                       REQUIRED — shared by all three experiments
    config.R                      path resolution
    load_bd.R                     BD matrix loader
  Exp160/                       ileal IEC, 3 cartridges, BD 1.9.1
    Exp160_Final.Rmd
    Exp160_AYEH_241108_FINAL.Rmd
    01_fig4_figS6.R
    02_figS7.R
    Exp160_versions.yaml
  Exp649/                       ileal IEC, IFNgR cKO multiplex, 2 cartridges, BD 1.10.1
    Exp649_Final.Rmd
    Exp649_AYEH_241104_FINAL.Rmd
    01_figS10_qc.R
    02_fig7_figS11.R
    Exp649_versions.yaml
  Exp80/                        ileal Marilyn donor CD4+ T cells, targeted panel, BD 1.8
    241221_Marilyn.Rmd
    02_figS3_from_deposit.R
    Exp80_versions.yaml
```

> **`common/` is not optional.** Every figure script resolves its helpers as
> `source(file.path(PKG, "02_figure_scripts", "common", "config.R"))`, where
> `PKG` is located by walking up for a `.ady3001_root` marker file. Keep that
> path and the marker, or edit two `source()` lines in each of the five scripts
> — which means touching analysis code and losing byte-identity with the
> verified archive. Keeping the path is preferred.

---

## Reproducibility, stated plainly

From the **deposited matrices**, all four main analyses reproduce the published
objects **100.00 % cell-for-cell** — identical cell sets and identical
cluster-size vectors. Fig S3 reproduces by two independent routes (the four
per-tag matrices, and the Combined matrix split by `Sample_Tag_Calls.csv`),
which give byte-identical results.

From **raw FASTQ**, Fig 7 / S11 does **not** reproduce: Louvain at resolution
0.5 sits on a community boundary, so a 0.001 % shift in molecule counts yields 7
ISC clusters instead of 9 (the cell set is essentially unchanged, Jaccard
0.997). Exp80's FASTQ→matrix step cannot be version-matched — BD never published
the v1.8 targeted CWL.

**Two corrections to the published Methods**, both found by running the code:

1. The mitochondrial filter is **`percent.mt < 40` for both** the IEC and ISC
   analyses. The Methods originally said 25 % for the IEC analysis and the Rmd
   carried a stale `25`; both were corrected. Filtering at 25 keeps 6,412 cells,
   where the published Fig 4 object holds **8,032 in 7 clusters** — and the
   corrected Rmd reproduces that object cell-for-cell.
2. The R version is **4.4.0**, not 4.0.3. All five published Seurat objects
   record `SeuratObject` 5.0.2 internally, which requires R ≥ 4.1.0.

Finally: **UMAP is defined only up to rotation and reflection**, so an embedding
may appear mirrored relative to the published panel. Fig S3A reproduces
horizontally mirrored. This is expected, not a defect.

---

## Licence

MIT — see `LICENSE`. Please cite both the article and the Zenodo archive; see
`CITATION.cff`.
