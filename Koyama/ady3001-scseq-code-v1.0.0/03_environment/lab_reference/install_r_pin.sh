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
#SBATCH --job-name=r_pin
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild/common/scripts/logs/r_pin-%j.out
#
# RESTORE THE VALIDATED R ENVIRONMENT.
#
# On 2026-09-18 the home library ~/R/x86_64-pc-linux-gnu-library/4.4 was updated
# in place. Seurat went 5.1.0 -> 5.5.1 and ggplot2 3.4.4 -> 4.0.3, and the
# rebuild stopped running at all:
#   "namespace 'rlang' 1.1.6 is already loaded, but >= 1.1.7 is required"
# Eleven of the 194 packages named in the validated sessionInfo drifted; none
# went missing. This installs those eleven, at their validated versions, into a
# library INSIDE Rebuild/ so the home library is never touched.
#
# Versions come from the sessionInfo.txt written by the 15-16 Sep runs that
# reproduced Fig 4/S6, S7, S10 and Fig 7/S11 cluster-for-cluster.
#
# dependencies = FALSE is deliberate: every dependency is already present at the
# validated version, and letting the installer "help" is what broke this.
set -euo pipefail
REB=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild
PIN=$REB/common/Rlib_pin
mkdir -p "$PIN"
# A failed install leaves 00LOCK-<pkg> behind and every later attempt then dies
# with "failed to lock directory". Clear them before starting.
rm -rf "$PIN"/00LOCK-*

module load R/4.4.0-gfbf-2023b
export R_LIBS_USER="$PIN:$REB/common/Rlib:/home/ayeh/R/x86_64-pc-linux-gnu-library/4.4"
echo "pin library: $PIN"

Rscript -e '
  pin <- strsplit(Sys.getenv("R_LIBS_USER"), ":", fixed = TRUE)[[1]][1]
  options(Ncpus = 8, repos = c(CRAN = "https://cloud.r-project.org"))
  if (!requireNamespace("remotes", quietly = TRUE)) install.packages("remotes", lib = pin)

  want <- c(vctrs = "0.6.5", lifecycle = "1.0.4", ggplot2 = "3.4.4", dplyr = "1.1.4",
            tidyr = "1.3.1", ggrepel = "0.9.6", cowplot = "1.1.3", patchwork = "1.3.0",
            httr = "1.4.7", Seurat = "5.1.0", scCustomize = "2.1.2")
  ## ORDER MATTERS. scCustomize byte-compiles against Seurat, so Seurat 5.1.0 has
  ## to be in the pin library first - otherwise the build picks up the home
  ## library Seurat 5.5.1, whose .so was compiled against GLIBC 2.38 and cannot
  ## even be dyn.load()ed on a gizmo node.

  for (p in names(want)) {
    cur <- tryCatch(as.character(packageVersion(p, lib.loc = pin)), error = function(e) NA)
    if (!is.na(cur) && cur == want[[p]]) { cat(sprintf("%-12s %-8s already pinned\n", p, cur)); next }
    cat(sprintf("--- installing %s %s\n", p, want[[p]]))
    remotes::install_version(p, version = want[[p]], lib = pin,
                             dependencies = FALSE, upgrade = "never", quiet = FALSE)
  }

  cat("\n=== result ===\n")
  ok <- TRUE
  for (p in names(want)) {
    got <- tryCatch(as.character(packageVersion(p, lib.loc = pin)), error = function(e) "ABSENT")
    flag <- if (identical(got, unname(want[[p]]))) "ok" else { ok <- FALSE; "WRONG" }
    cat(sprintf("%-12s want %-8s got %-8s %s\n", p, want[[p]], got, flag))
  }
  if (!ok) quit(status = 1)
'
echo "### DONE"
