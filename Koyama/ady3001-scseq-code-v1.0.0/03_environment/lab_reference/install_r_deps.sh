#!/bin/bash
# ===================================================================
# LAB REFERENCE ONLY - THIS SCRIPT WILL NOT RUN OUTSIDE THE HILL LAB
# ALLOCATION AT FRED HUTCH.
#
# It hardcodes an #SBATCH --output directory, the target library and
# /home/ayeh/R/..., and it passes dependencies = FALSE, which is only
# safe when a complete validated library already exists.
#
# To build the environment, use:  03_environment/install_packages.R
#
# This file is deposited because it is the record of how the pinned
# library was actually built for the published runs.
# ===================================================================
#SBATCH --partition=campus-new
#SBATCH --job-name=r_deps
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild/common/scripts/logs/r_deps-%j.out
#
# Two packages the existing Rmds load are absent from the R 4.4 library:
#   ggpubr  - stat_compare_means(), which draws every Wilcoxon bracket in
#             Fig 4C/D, S7D, S10B and S11. Without it those panels cannot be drawn.
#   ArchR   - used for exactly one thing, paletteContinuous(n=8), which defines
#             rna_cols, the gradient of every module-score FeaturePlot.
#
# They install into a library INSIDE this Rebuild folder, not into
# ~/R/x86_64-pc-linux-gnu-library/4.4. Two reasons: the home library carries 22
# stale 00LOCK-* directories from interrupted installs in 2024-2025 that make
# install.packages() fail with "failed to lock directory", and a rebuild should
# not mutate the environment it is trying to document.
#
# ArchR needs DirichletMultinomial, which needs GSL headers; the bare gcc on the
# node has none, so the GSL module is loaded for the same toolchain as R 4.4.0.
set -euo pipefail
REB=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild
LIB=$REB/common/Rlib
mkdir -p "$LIB"

module load R/4.4.0-gfbf-2023b
module load GSL/2.7-GCC-13.2.0
# IMPORTANT: R_LIBS_USER REPLACES the default user library in .libPaths().
# Setting it to $LIB alone hides ~/R/.../4.4, so install.packages() would
# rebuild Seurat's whole dependency tree into $LIB at newer versions than the
# ones the analysis was run against. Both libraries, $LIB first.
export R_LIBS_USER="$LIB:/home/ayeh/R/x86_64-pc-linux-gnu-library/4.4"
echo "target library: $LIB"
echo "gsl-config: $(command -v gsl-config)  $(gsl-config --version 2>/dev/null)"

Rscript -e '
  lib <- strsplit(Sys.getenv("R_LIBS_USER"), ":", fixed = TRUE)[[1]][1]
  options(Ncpus = 8, repos = c(CRAN = "https://cloud.r-project.org"))
  cat("libPaths:\n"); print(.libPaths())

  need <- function(p) !requireNamespace(p, quietly = TRUE)

  if (need("ggpubr"))   install.packages("ggpubr",   lib = lib)
  if (need("BiocManager")) install.packages("BiocManager", lib = lib)
  if (need("DirichletMultinomial"))
      BiocManager::install("DirichletMultinomial", lib = lib, ask = FALSE, update = FALSE)
  if (need("devtools")) install.packages("devtools", lib = lib)
  if (need("ArchR"))
      devtools::install_github("GreenleafLab/ArchR", ref = "master", lib = lib,
                               repos = BiocManager::repositories(), upgrade = "never")

  for (p in c("ggpubr","ArchR")) {
    cat(sprintf("%-8s %s\n", p,
        if (requireNamespace(p, quietly = TRUE)) as.character(packageVersion(p)) else "FAILED"))
  }
  if (requireNamespace("ArchR", quietly = TRUE)) {
    cat("rna_cols =", paste(ArchR::paletteContinuous(n = 8)[c(1:3, 6:8)], collapse = " "), "\n")
  }
'
