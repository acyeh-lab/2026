# ady3001 — code deposit and its builders

Two things live here, and the distinction matters when you go to change
something.

```
ady3001-scseq-code-v1.0.0/   THE DELIVERABLE — what is uploaded to Zenodo and
                             pushed to GitHub. 60 files. GENERATED: do not edit
                             anything in this directory by hand.
builders/                    THE SOURCE — the scripts that generate it.
                             Edit these, then rebuild.
```

## Rebuilding

```bash
module load Python/3.11.5-GCCcore-13.2.0
python3 builders/build_zenodo_package.py     # wipes and regenerates the package
python3 builders/build_zenodo_report.py      # regenerates the HTML report
```

`build_zenodo_package.py` deletes `ady3001-scseq-code-v1.0.0/` and rebuilds it
from the working copies under `../Rebuild/` and from the original R Markdown.
Anything typed into the package directly is lost on the next build — which is
the point: the package cannot drift from its sources.

## What the package is

The complete analysis code for Koyama *et al.*, *Science Immunology* (ady3001).
It regenerates all seven scRNA-seq figures — **Fig 4, 7, S3, S6, S7, S10,
S11** — from the matrices deposited in NCBI GEO under **GSE348009**.

It exists because the GitHub repository the manuscript's Methods cite is
incomplete: its `Exp160_Final.Rmd` is the pre-revision version, missing all of
Figure S7 and Figure S6C, and the Figure S3 code was never pushed at all.

See `ady3001-scseq-code-v1.0.0/README.md` for how to run it.

## Provenance of the builders

The authoritative copies live at:

| file | home |
|---|---|
| `build_zenodo_package.py` | `../Rebuild/zenodo/` |
| `package_docs.py` | `../Rebuild/zenodo/` |
| `run_package_test.sh` | `../Rebuild/zenodo/` |
| `build_zenodo_report.py` | `../Sci_Imm_Revision/` |

The copies here were byte-identical to those at commit time. If you edit one,
edit it in **one** place and re-copy, or the two will drift. `sync_builders.sh`
checks.

## Verification

- `ady3001-scseq-code-v1.0.0/verify_package.sh` — checksums, path escapes,
  parse checks and internal consistency. Needs neither data nor R packages.
- `builders/run_package_test.sh` — SLURM job that runs the **packaged** scripts
  against a clean room of only the 28 deposited GEO files, end to end.

Result of that test (job 8654854, 2026-09-21): **124 panels, 0 empty**, and
every cell count, cluster count and result table identical to the published
objects.

## Known limits

Stated in full in `ady3001-scseq-code-v1.0.0/README.md`. The short version:

- From the **deposited matrices**, everything reproduces 100 % cell-for-cell.
- From **raw FASTQ**, Fig 7 / S11 does *not* — Louvain at resolution 0.5 sits on
  a community boundary, so a 0.001 % molecule shift yields 7 ISC clusters
  instead of 9. The cell set is essentially unchanged (Jaccard 0.997).
- Exp80's FASTQ→matrix step cannot be version-matched; BD never published the
  v1.8 targeted CWL.
- UMAP orientation is defined only up to rotation and reflection.
