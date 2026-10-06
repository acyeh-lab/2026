# Koyama *et al.*, *Science Immunology* — single-cell RNA-seq analysis code

Analysis code for:

> **IFN-γ-driven MHC class II expression by intestinal epithelial cells dictates
> local cytolytic Th1 differentiation and intestinal stem cell loss**
> Koyama M, Yeh AC, Haeseleer F, Ensbey KS, Bhise SS, Schuster IS, Legg SRW, Nelson E, Sekiguchi T, Nemychenkov NS, Takahashi S, Zhang P, Minnie SA, Hippe DS, Degli-Esposti MA, Clouston AD, Furlan SN, Hill GR. *Science Immunology*

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

---

## The executable R Markdown files, the figures they generate, and what they read

Transcribed from the notebooks above, path-parameterised, and verified to
reproduce the published objects cell-for-cell. These are the ones to run.

| Manuscript figure | Panels | R Markdown | Reads (processed file) | GEO sample |
|---|---|---|---|---|
| **Fig 4B–D** | 22 | `Exp160/01_fig4_figS6.Rmd` | `cartridge1_RSEC_MolsPerCell.csv`<br>`cartridge2_RSEC_MolsPerCell.csv` | GSM10065191<br>GSM10065192 |
| **Fig S6A–E** | 17 | `Exp160/01_fig4_figS6.Rmd` | *(same as above — one clustering)* | GSM10065191<br>GSM10065192 |
| **Fig S7B–E** | 26 | `Exp160/02_figS7.Rmd` | `cartridge2_RSEC_MolsPerCell.csv`<br>`cartridge3_RSEC_MolsPerCell.csv` | GSM10065192<br>GSM10065193 |
| **Fig S10A–D** | 7 | `Exp649/01_figS10_qc.Rmd` | `Cart1_RSEC_MolsPerCell.csv`<br>`Cart2_RSEC_MolsPerCell.csv` | GSM10065194<br>GSM10065195 |
| **Fig 7B–F + Fig S11A–C** | 39 | `Exp649/02_fig7_figS11.Rmd` | `all_cells_processed.RDS`<br>*(written by `01_figS10_qc.Rmd`)* | — |
| **Fig S3A–C** | 5 | `Exp80/02_figS3_from_deposit.Rmd` | the four `*_SampleTag0{5,6,7,8}_mm_RSEC_MolsPerCell.csv`<br>**or** `Combined_…_RSEC_MolsPerCell.csv` + `…_Sample_Tag_Calls.csv` | GSM10065196 |

**124 panels total** (122 PDF + 2 PNG); 8 are QC plots, not manuscript panels.

Each file is chunked by figure, with an H2 heading and a navigable table of
contents in the knitted HTML, so a given panel can be found, re-run and
commented on in isolation. For example `01_fig4_figS6.Rmd` carries chunks
`sec3-figure-4b`, `sec4-figure-4c-msigdb-c5-module-scores` and
`sec7-figure-s6c-isc-progenitor-markers`.

Two figures cannot be given their own file. Fig 7 and Fig S11 share one row
because 11 panels are Fig 7 only, 10 are Fig S11 only and **18 are labelled as
spanning both**; likewise `01_fig4_figS6.Rmd` produces Fig 4 and Fig S6 from a
single clustering. Splitting either would require re-clustering.

### Notes on the inputs

`cartridge2` is read by **both** Exp160 files and re-clustered separately in
each — intentional, not duplication.

**RSEC, not DBEC.** WTA Rhapsody applies RSEC only; the `_DBEC_` files are
deposited for completeness and read by nothing here. Exp80 is a *targeted*
panel, where DBEC would be meaningful — but the published analysis read RSEC, so
RSEC is what these files use.

**Fig S3 is derived two independent ways** and the two agree byte-for-byte: from
the four deposited per-tag matrices, and from the deposited Combined matrix
split by `Sample_Tag_Calls.csv`.

A GEO download is flat; these files expect per-cartridge directories
(`cartridge1/`…, and `Cart1/`/`Cart2/` with a capital C for Exp649) under
`$ADY3001_DATA`. `tools/unpack_geo_download.sh` builds that tree.

### Run order

```
Exp160:  01_fig4_figS6.Rmd   and   02_figS7.Rmd        independent
Exp649:  01_figS10_qc.Rmd   ──►   02_fig7_figS11.Rmd   SEQUENTIAL
Exp80:   02_figS3_from_deposit.Rmd                     standalone
```

`Exp649/02_fig7_figS11.Rmd` does **not** read the matrices — it reads
`all_cells_processed.RDS` written by `01_figS10_qc.Rmd`, so that file runs first.

### Knitting

The code locates the package root by walking up for a `.ady3001_root` marker, so
knit with `knit_root_dir` set to that root, or run from a directory beneath it.
Results are written to `$ADY3001_OUT`, default `./ady3001_output`.

```r
rmarkdown::render("Exp649/01_figS10_qc.Rmd", knit_root_dir = "<package root>")
```

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

One subfolder per experiment; each holds its executable R Markdown, its original
notebook, and its version manifest.

```
Koyama/
  README.md                        this file
  r_packages.yml                   all 195 packages, for install
  environment.yml                  conda environment
  common/                          REQUIRED - shared by all three experiments
    config.R                         path resolution
    load_bd.R                        BD matrix loader
  Exp160/                          ileal IEC, 3 cartridges, BD 1.9.1
    01_fig4_figS6.Rmd                Fig 4B-D, S6A-E   <- run this
    02_figS7.Rmd                     Fig S7B-E         <- run this
    Exp160_Final.Rmd                 the original notebook
    Exp160_versions.yaml
  Exp649/                          ileal IEC, IFNgR cKO multiplex, 2 cartridges, BD 1.10.1
    01_figS10_qc.Rmd                 Fig S10A-D        <- run this FIRST
    02_fig7_figS11.Rmd               Fig 7B-F, S11A-C  <- then this
    Exp649_Final.Rmd                 the original notebook
    Exp649_versions.yaml
  Exp80/                           ileal Marilyn donor CD4+ T cells, targeted panel, BD 1.8
    02_figS3_from_deposit.Rmd        Fig S3A-C         <- run this
    241221_Marilyn.Rmd               the original notebook
    Exp80_versions.yaml
```

> **`common/` is not optional.** Every figure script resolves its helpers as
> `source(file.path(PKG, "02_figure_scripts", "common", "config.R"))`, where
> `PKG` is located by walking up for a `.ady3001_root` marker file. Keep that
> path and the marker, or edit two `source()` lines in each of the five scripts
> — which means touching analysis code and losing byte-identity with the
> verified archive. Keeping the path is preferred.

---

## Licence

MIT — see `LICENSE`. Please cite both the article and the Zenodo archive; see
`CITATION.cff`.
