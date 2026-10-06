# Environment

## The versions that produced the published figures

There is **no original `sessionInfo`** for the published analysis: neither final
Rmd was ever knitted to a rendered record. The eight HTML files in the lab's
`rmd/` directories are 2020-2022 exploratory versions running R 4.0.3-4.2.0 and
Seurat 3.2.3-4.1.1, and they do **not** describe the published analysis.

What is authoritative is the environment in which the published objects are
reproduced cluster-for-cluster, recorded in the `sessionInfo_*.txt` files here:

| | Exp160 / Exp649 | Exp80 (Fig S3) |
|---|---|---|
| R | **4.4.0** | **4.3.2** |
| Seurat | **5.1.0** | **5.0.0** |
| SeuratObject | 5.0.2 | 5.0.1 |
| scCustomize | 2.1.2 | 2.1.1 |
| also | monocle3 1.3.7 (Exp160), fgsea 1.30.0 (Exp649) | - |

The two experiments genuinely used **different Seurat versions**. 5.1.0 and
5.0.0 are not a typo for one another.

### Independent corroboration

All five published Seurat objects carry `SeuratObject` **5.0.2** in their
`@version` slot. `SeuratObject` 5.0.2 was packaged 2024-05-07 and declares
`Depends: R (>= 4.1.0)`.

> **The manuscript's Statistical analysis section says "R (ver. 4.0.3) for
> RNAseq data". That is not possible** - R 4.0.3 (October 2020) cannot load a
> SeuratObject 5.x object, and the published objects were written in November
> 2024 and August 2025. The correct statement is R 4.4.0 / Seurat 5.1.0 for the
> IEC and ISC experiments and R 4.3.2 / Seurat 5.0.0 for the Marilyn T-cell
> experiment.

## Why a pinned library is not optional

On 2026-09-18 the home R library that held these packages was updated in place.
Eleven packages drifted - **Seurat 5.1.0 -> 5.5.1** and **ggplot2 3.4.4 ->
4.0.3** among them - and the analysis stopped running the same day: Seurat would
not even load. ggplot2 4.x is the S7 rewrite, which breaks Seurat 5.1.0's
`patchwork & theme` idiom and kills every multi-feature `VlnPlot`.

Reproducibility that depended on a mutable home directory lasted **three days**.

`install_r_pin.sh` installs the drifted packages at their validated versions
into a library of your choosing, which `config.R` then places first on
`.libPaths()`. Two traps it already handles:

- **Seurat must be installed before scCustomize**, which byte-compiles against
  it; otherwise the build reaches for whatever Seurat is already installed.
- A failed install leaves a `00LOCK-<pkg>` directory and every later attempt
  dies with "failed to lock directory". The script clears them first.

## Do not upgrade ggpubr

`install_ggpubr.sh` pins **ggpubr 0.6.0** from a 2024-11-08 CRAN snapshot. The
newest version that installs (0.6.1) requires ggplot2 >= 3.5.2, which pulls
ggplot2 4.x into the library where it shadows 3.4.4 - the exact break above.

## Modules (Fred Hutch cluster)

    module load R/4.4.0-gfbf-2023b
    module load Pandoc/2.13                  # only to knit the Rmds
    module load HDF5/1.14.5-gompi-2024a      # only for hdf5r / m3addon

R shares libraries by MAJOR.MINOR, so 4.4.0 / 4.4.1 / 4.4.2 all use
`.../library/4.4`. R 4.5.x would need everything reinstalled.
