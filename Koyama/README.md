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

## The executable R Markdown files, the figures they generate, and what they read
| Manuscript figure | Panels | R Markdown | Reads (processed file) | GEO sample |
|---|---|---|---|---|
| **Fig 4B–D** | 22 | `Exp160/01_fig4_figS6.Rmd` | `cartridge1_RSEC_MolsPerCell.csv`<br>`cartridge2_RSEC_MolsPerCell.csv` | GSM10065191<br>GSM10065192 |
| **Fig S6A–E** | 17 | `Exp160/01_fig4_figS6.Rmd` | *(same as above — one clustering)* | GSM10065191<br>GSM10065192 |
| **Fig S7B–E** | 26 | `Exp160/02_figS7.Rmd` | `cartridge2_RSEC_MolsPerCell.csv`<br>`cartridge3_RSEC_MolsPerCell.csv` | GSM10065192<br>GSM10065193 |
| **Fig S10A–D** | 7 | `Exp649/01_figS10_qc.Rmd` | `Cart1_RSEC_MolsPerCell.csv`<br>`Cart2_RSEC_MolsPerCell.csv` | GSM10065194<br>GSM10065195 |
| **Fig 7B–F + Fig S11A–C** | 39 | `Exp649/02_fig7_figS11.Rmd` | `all_cells_processed.RDS`<br>*(written by `01_figS10_qc.Rmd`)* | — |
| **Fig S3A–C** | 5 | `Exp80/02_figS3_from_deposit.Rmd` | the four `*_SampleTag0{5,6,7,8}_mm_RSEC_MolsPerCell.csv`<br>**or** `Combined_…_RSEC_MolsPerCell.csv` + `…_Sample_Tag_Calls.csv` | GSM10065196 |

### Notes on the inputs
**RSEC, not DBEC.** WTA Rhapsody applies RSEC only; the `_DBEC_` files are
deposited for completeness and read by nothing here. 

### Running them
**Edit one line.** Each file opens with a `DATA` line in its first chunk. Point
it at wherever you downloaded that experiment's processed matrices from
[GSE348009](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE348009):
```r
DATA <- "~/GSE348009/Exp160"     # must contain cartridge1/ and cartridge2/
```


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
