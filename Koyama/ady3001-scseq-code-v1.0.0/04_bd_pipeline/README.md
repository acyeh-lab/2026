# Part 1 - FASTQ to expression matrices

**You do not need this to regenerate the figures.** GEO accession GSE348009
carries the expression matrices, and `02_figure_scripts/` starts from those.
This directory is here so the path from raw reads is auditable and re-runnable.

## Pinned versions - these are not interchangeable

| | Exp160 | Exp649 |
|---|---|---|
| BD pipeline | `bdgenomics/rhapsody:1.9.1` | `bdgenomics/rhapsody:1.10.1` |
| CWL | `rhapsody_wta_1.9.1.cwl` | `rhapsody_wta_1.10.1.cwl` |
| Genome | `GRCm38-PhiX-gencodevM19-20181206` | same |
| AbSeq panel | 4 pAbO | 7 pAbO (4 of them CD326 sample hashes) |

Both versions come from the experiments' own `Metrics_Summary.csv` headers.
Running a current BD release instead would not be a reproduction: v2.x changed
the reference format, the cell-calling algorithm and the outputs.

Exp80 used the **targeted** Immune Response panel on BD pipeline v1.8. The v1.8
targeted CWL is not published by BD and is not in the v1.8 container, so that
experiment's FASTQ-to-matrix step is **not version-matched reproducible**. The
deposited matrices are BD's original v1.8 output.

## The AbSeq references

The two AbSeq FASTAs named in the metrics headers were Seven Bridges inputs and
were not retained. Both are reconstructible exactly, and
`rebuild_abseq_reference.py` does it:

- the **panel** is the header row of each `*_RSEC_MolsPerCell.csv`, which lists
  every target in BD's four-field form
  (`CD326:G8.8-AMM2281|Epcam|AMM2281|pAbO`) - that string *is* the FASTA record
  name
- the **barcodes** come from BD's public cumulative reference,
  `s3://bd-rhapsody-public/AbSeq-references/BDAbSeq_allReference_<date>.fasta`,
  using the last release predating each experiment's own reference date
  (2020-08-20 for Exp160, 2022-03-17 for Exp649)

Cross-checked against the four printed BD data sheets; all four barcodes match.

The rebuilt FASTAs are in `abseq/`. They are **machine reconstructions**, and
are provided for re-running the pipeline only - they were deliberately not
deposited to GEO.

Still genuinely missing: Exp160's `combined_extra_seq.fasta` (supplemental
transgene sequences). No transgene name appears among Exp160's 21,907 gene
columns, so it contributed no detected target, but the Exp160 re-run is
therefore declared reference-incomplete rather than identical.

## How close the re-run came

Across all five cartridges, against BD's original Seven Bridges output:

- **feature sets and cell sets identical** in all five - same counts, zero
  entries on one side only
- total difference **0.0009-0.0013% of molecules**; median 1 molecule per
  differing cell; Pearson r = 1.000000
- for Exp160 every *gene* column is identical; the entire discrepancy sits in
  the four AbSeq channels

Re-running the figure scripts from those rebuilt matrices reproduces Fig 4, S6
and S7 identically. **Fig 7 / S11 does not reproduce from rebuilt matrices** -
Louvain at resolution 0.5 sits near a community boundary, so a 0.001% difference
in molecules renumbers the 12-cluster map and yields 7 ISC communities instead
of 9. The cell set is essentially unchanged (Jaccard 0.997). The script detects
this and refuses to claim a reproduction.

This is why **GEO carries the original matrices**, which reproduce every figure
exactly.

## Traps

- Singularity may be unable to loop-mount a `.sif` and will unpack ~6 GB per
  container start; `run_bd_pipeline.sh` builds one sandbox per job on local
  scratch and passes `--singularity-sandbox-path`.
- BD's v1.10.1 CWL evaluates a VDJ RAM hint over a null input when no VDJ
  library is present, and cwltool 3.2 refuses at the very end of an otherwise
  complete run. `patch_cwl_nullsafe_ram.py` writes a `.nullsafe.cwl`.
