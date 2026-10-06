#!/usr/bin/env Rscript
## ===========================================================================
## Does the GEO deposit, on its own, regenerate the published objects?
##
## Compares, for each of the four ady3001 analyses:
##   A  the object the figures were made from      (Exp*/cds/*.RDS, published)
##   B  the clean-room run                          (--source deposit)
##   C  the in-place run from the lab copy          (--source original)
##
## B vs A is the reproducibility claim. B vs C checks that restricting the
## inputs to the 44 deposited files changed nothing at all.
##
## Reported per analysis: cell sets, cluster counts, cluster sizes, and the
## fraction of cells whose cluster maps 1:1 between the two labellings
## (clusters can be renumbered; the partition is what matters).
## ===========================================================================
suppressPackageStartupMessages({ library(Seurat) })
ROOT <- "/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024"
REB  <- file.path(ROOT, "Rebuild")

cases <- list(
  list(name = "Fig 4 / S6   (Exp160 cart1+cart2)",
       pub  = file.path(ROOT, "Exp160/cds/241108v2_processed.RDS"),
       dep  = file.path(REB, "Exp160/02_r_rebuild/out_deposit_RSEC/cds/cart1_cart2_processed.RDS"),
       org  = file.path(REB, "Exp160/02_r_rebuild/out_original_RSEC/cds/cart1_cart2_processed.RDS")),
  list(name = "Fig S7       (Exp160 cart2+cart3)",
       pub  = file.path(ROOT, "Exp160/cds/250814_cart2_3_processed.RDS"),
       dep  = file.path(REB, "Exp160/02_r_rebuild/outS7_deposit_RSEC/cds/cart2_cart3_processed.RDS"),
       org  = file.path(REB, "Exp160/02_r_rebuild/outS7_original_RSEC/cds/cart2_cart3_processed.RDS")),
  list(name = "Fig S10      (Exp649 all cells)",
       pub  = file.path(ROOT, "Exp649/cds/241104_processed.RDS"),
       dep  = file.path(REB, "Exp649/02_r_rebuild/outS10_deposit_RSEC/cds/all_cells_processed.RDS"),
       org  = file.path(REB, "Exp649/02_r_rebuild/outS10_original_RSEC/cds/all_cells_processed.RDS")),
  list(name = "Fig 7 / S11  (Exp649 ISC subset)",
       pub  = file.path(ROOT, "Exp649/cds/241105_processed.RDS"),
       dep  = file.path(REB, "Exp649/02_r_rebuild/outFig7_deposit_RSEC/cds/isc_processed.RDS"),
       org  = file.path(REB, "Exp649/02_r_rebuild/outFig7_original_RSEC/cds/isc_processed.RDS")))

clus <- function(o) { x <- as.character(o$seurat_clusters); names(x) <- colnames(o); x }

compare <- function(lab, a, b) {
  ca <- clus(a); cb <- clus(b)
  same_cells <- setequal(names(ca), names(cb))
  cat(sprintf("   %-28s cells %d vs %d  %s\n", lab, length(ca), length(cb),
              ifelse(same_cells, "IDENTICAL SET", "*** DIFFERENT SET ***")))
  shared <- intersect(names(ca), names(cb))
  cat(sprintf("   %-28s clusters %d vs %d   sizes %s\n", "",
              length(unique(ca)), length(unique(cb)),
              ifelse(identical(sort(unname(table(ca))), sort(unname(table(cb)))),
                     "IDENTICAL", "differ")))
  tb <- table(ca[shared], cb[shared])
  ## best 1:1 mapping: for each published cluster take its largest counterpart
  agree <- sum(apply(tb, 1, max)) / length(shared) * 100
  cat(sprintf("   %-28s cells in the majority-matched cluster: %.2f%%\n", "", agree))
  if (agree < 100) print(tb)
  invisible(agree)
}

for (cs in cases) {
  cat("\n================================================================\n")
  cat(cs$name, "\n")
  for (f in c(cs$pub, cs$dep, cs$org)) if (!file.exists(f)) cat("   MISSING:", f, "\n")
  if (!all(file.exists(c(cs$pub, cs$dep, cs$org)))) next
  pub <- readRDS(cs$pub); dep <- readRDS(cs$dep); org <- readRDS(cs$org)
  cat("-- deposit run vs PUBLISHED object\n");            compare("deposit vs published", pub, dep)
  cat("-- deposit run vs lab-copy run (same script)\n");  compare("deposit vs original",  org, dep)
  rm(pub, dep, org); gc(verbose = FALSE)
}
cat("\n=== DONE ===\n")
