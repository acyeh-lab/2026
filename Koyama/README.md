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
| Manuscript figure  | R Markdown | Reads (processed file) | GEO sample |
|---|---|---|---|
| **Fig 4B–D** | `Exp160/01_fig4_figS6.Rmd` | `cartridge1_RSEC_MolsPerCell.csv`<br>`cartridge2_RSEC_MolsPerCell.csv` | GSM10065191<br>GSM10065192 |
| **Fig S6A–E** | `Exp160/01_fig4_figS6.Rmd` | *(same as above)* | GSM10065191<br>GSM10065192 |
| **Fig S7B–E** | `Exp160/02_figS7.Rmd` | `cartridge2_RSEC_MolsPerCell.csv`<br>`cartridge3_RSEC_MolsPerCell.csv` | GSM10065192<br>GSM10065193 |
| **Fig S10A–D** | `Exp649/01_figS10_qc.Rmd` | `Cart1_RSEC_MolsPerCell.csv`<br>`Cart2_RSEC_MolsPerCell.csv` | GSM10065194<br>GSM10065195 |
| **Fig 7B–F + Fig S11A–C** | `Exp649/02_fig7_figS11.Rmd` | `all_cells_processed.RDS`<br>*(written by `01_figS10_qc.Rmd`)* | — |
| **Fig S3A–C** | `Exp80/01_figS3.Rmd` | `Combined_…_RSEC_MolsPerCell.csv` + `…_Sample_Tag_Calls.csv` | GSM10065196 |

### Running them
**Edit one line.** Each file opens with a `DATA` line in its first chunk. Point
it at wherever you downloaded that experiment's processed matrices from
[GSE348009](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE348009):
```r
DATA <- "~/GSE348009/Exp160"     # must contain cartridge1/ and cartridge2/
```

### Reproducibility:
Running these files reproduces every cell count, cluster assignment and expression value. UMAP embeddings may differ between computing environments; the clusters they display are identical.
