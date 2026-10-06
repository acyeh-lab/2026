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
#SBATCH --job-name=ggpubr
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild/common/scripts/logs/ggpubr-%j.out
#
# Installing ggpubr here is harder than it looks, and getting it wrong silently
# breaks Seurat. Two traps, both hit on 2026-09-15:
#
# 1. ggpubr cannot be installed from today's CRAN on R 4.4.0 at all. Its chain is
#    ggpubr -> rstatix -> car -> pbkrtest -> doBy -> Deriv, and the current Deriv
#    (4.3.5) declares R (>= 4.5). install.packages() reports that only as a
#    warning and then fails five packages with no error.
#
# 2. Taking the newest ggpubr that *does* install (0.6.1) drags in
#    ggplot2 (>= 3.5.2), so ggplot2 4.0.3 lands in this library and SHADOWS the
#    ggplot2 3.4.4 in the home library. ggplot2 4.x is the S7 rewrite, and
#    Seurat 5.1.0's plotting uses `patchwork & theme`, which S7 does not
#    dispatch. Every multi-feature VlnPlot then dies with
#      Can't find method for generic `&(e1, e2)`: e1 <patchwork>, e2 <theme>
#    i.e. the fix for the missing package breaks the package that needed it.
#
# So: pin to a dated CRAN snapshot from 2024-11-08 (the date of
# Exp160_AYEH_241108_FINAL.Rmd). That gives ggpubr 0.6.0 - the same version in
# Albert's own R 4.2 library - which needs only ggplot2 (>= 3.4.0), satisfied by
# the home library's 3.4.4. Nothing shadows anything.
set -euo pipefail
REB=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild
LIB=$REB/common/Rlib
HOME_LIB=/home/ayeh/R/x86_64-pc-linux-gnu-library/4.4
SNAPSHOT=https://packagemanager.posit.co/cran/2024-11-08

module load R/4.4.0-gfbf-2023b
export R_LIBS_USER="$LIB:$HOME_LIB"

# Drop anything in this library that also exists in the home or module library,
# plus the ggpubr chain built against it. These are all re-installable; nothing
# outside this Rebuild folder is touched.
echo "-- pruning shadowing packages from $LIB"
for p in ggplot2 dplyr rlang tidyr cowplot vctrs lifecycle \
         ggpubr rstatix car pbkrtest doBy Deriv microbenchmark forecast ; do
  [[ -d "$LIB/$p" ]] && { echo "   rm $p ($(cat $LIB/$p/DESCRIPTION | grep -m1 ^Version:))"; rm -rf "$LIB/$p"; }
done
rm -rf "$LIB"/00LOCK-*

echo "-- installing the ggpubr chain from $SNAPSHOT"
SNAPSHOT=$SNAPSHOT Rscript -e '
  lib  <- strsplit(Sys.getenv("R_LIBS_USER"), ":", fixed = TRUE)[[1]][1]
  options(Ncpus = 8, repos = c(CRAN = Sys.getenv("SNAPSHOT")))
  for (p in c("Deriv","microbenchmark","doBy","pbkrtest","car","rstatix","ggpubr")) {
    if (!requireNamespace(p, quietly = TRUE)) install.packages(p, lib = lib)
  }
  cat("\n-- versions actually in use --\n")
  for (p in c("ggplot2","ggpubr","rstatix","car","Seurat","patchwork","ArchR")) {
    ok <- requireNamespace(p, quietly = TRUE)
    cat(sprintf("%-10s %-10s %s\n", p,
        if (ok) as.character(packageVersion(p)) else "MISSING",
        if (ok) dirname(find.package(p)) else ""))
  }
'

echo "-- functional test: the exact call that broke before"
Rscript -e '
  suppressPackageStartupMessages({library(Seurat); library(ggpubr); library(ggplot2)})
  set.seed(1)
  m <- matrix(rpois(4000, 5), nrow = 100,
              dimnames = list(paste0("g", 1:100), paste0("c", 1:40)))
  s <- CreateSeuratObject(counts = m)
  s$grp <- rep(c("a","b"), each = 20)
  s <- NormalizeData(s, verbose = FALSE)
  s$log_RNA <- log10(s$nCount_RNA)
  p <- VlnPlot(s, features = c("nFeature_RNA","nCount_RNA","log_RNA"),
               group.by = "grp", ncol = 3, pt.size = 0)
  print(class(p))
  q <- VlnPlot(s, features = "nCount_RNA", group.by = "grp", pt.size = 0) +
       stat_compare_means(comparisons = list(c("a","b")), method = "wilcox.test")
  tmp <- tempfile(fileext = ".pdf"); pdf(tmp); print(p); print(q); dev.off()
  cat("multi-feature VlnPlot + stat_compare_means rendered OK:", file.exists(tmp), "\n")
  cat("ArchR rna_cols:", paste(ArchR::paletteContinuous(n=8)[c(1:3,6:8)], collapse=" "), "\n")
'
