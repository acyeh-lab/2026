#!/usr/bin/env Rscript
## ===========================================================================
## Exp80 - Figure S3 A-C   (Marilyn T cells, ileal EL vs LP, targeted panel)
##
## Transcribed from /fh/fast/hill_g/Rhapsody/Marilyn/rmd/241221_Marilyn.Rmd
## (SNF, 21 Dec 2024). Every analysis step below is that Rmd's, unchanged.
##
## Deviations, all forced, all path/environment only:
##   * ROOT_DIR in the Rmd is chosen by switch() on hostname, with cases for UW,
##     SCRI, three named Macs and an AWS box - none for rhino/gizmo. Replaced
##     with the real location of the data.
##   * The Rmd is knitted with prettydoc; this runs as a plain Rscript so no
##     prettydoc dependency is needed.
##   * NOTE ON VERSIONS: the original ran R 4.3.2 / Seurat 5.0.0 on macOS arm64
##     (sessionInfo in 241221_Marilyn.html). This runs whatever is loaded, which
##     is R 4.4.0 / Seurat 5.1.0. That is a DELIBERATE version-drift test: it
##     asks whether the figure survives the version change, which is what a
##     reader re-running the deposit would actually face. It is NOT a
##     version-matched reproduction.
##
## Usage: Rscript 01_figS3.R
## ===========================================================================
## --- path resolution (Zenodo package) ---------------------------------------
## These lines replace the hardcoded lab paths of the working copy. Every other
## change to this file is also path-only; no analysis line differs from the
## script that produced the published figures. The complete diff against the
## working copy is shipped at 05_verification/path_rewrite.diff - read it rather
## than taking this comment's word for it.
local({
  a <- commandArgs(FALSE)
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  d <- if (length(f)) dirname(normalizePath(f[1])) else normalizePath(getwd())
  repeat {
    if (file.exists(file.path(d, ".ady3001_root"))) break
    p <- dirname(d)
    if (p == d) stop("cannot locate the package root (.ady3001_root marker)")
    d <- p
  }
  assign("PKG", d, envir = .GlobalEnv)
})
source(file.path(PKG, "02_figure_scripts", "common", "config.R"))

suppressPackageStartupMessages({
  library(Seurat); library(ggplot2); library(dplyr); library(Matrix)
  library(scCustomize); library(data.table)
})

DATA_DIR <- Sys.getenv("ADY3001_EXP80_FULL", "/fh/fast/hill_g/Rhapsody/Marilyn/data")  # lab-only: the 8-tag data is not on GEO
OUT <- file.path(OUT_ROOT, "Exp80", "out_figS3")
FIG <- file.path(OUT, "figs")
for (d in c(OUT, FIG)) {
  dir.create(d, recursive = TRUE, showWarnings = FALSE)
  if (!dir.exists(d)) stop("could not create ", d)
}
sink(file.path(OUT, "figS3_report.txt"), split = TRUE)
cat("=== Exp80 fig. S3 rebuild ===\n")
cat("R       :", R.version.string, "\n")
cat("Seurat  :", as.character(packageVersion("Seurat")), "\n")
cat("original ran R 4.3.2 / Seurat 5.0.0 - this is a version-drift test\n\n")

## --- the Rmd's loader, verbatim in behaviour --------------------------------
folders <- as.list(list.files(DATA_DIR, include.dirs = TRUE)[
             grep("_mm$", list.files(DATA_DIR, include.dirs = TRUE))])
names(folders) <- 1:8
cat("sample-tag folders found (alphabetical, mapped 1:8):\n")
for (i in seq_along(folders)) cat(sprintf("   %d -> %s\n", i, folders[[i]]))

files <- lapply(folders, function(folder) {
  f2 <- file.path(DATA_DIR, folder)
  list.files(f2, full.names = TRUE)[grep("_mm_RSEC_MolsPerCell.csv$", list.files(f2))]
})
stopifnot(all(lengths(files) == 1))

dat  <- lapply(files, function(f) t(as.matrix(data.table::fread(f), rownames = 1)))
dat2 <- lapply(dat, function(m) { rownames(m) <- sapply(strsplit(rownames(m), "\\|"), "[[", 1); m })
mat  <- Matrix(do.call(cbind, dat2), sparse = TRUE)
colnames(mat) <- make.unique(colnames(mat))

meta <- data.frame(cell.names = colnames(mat),
                   sample_no  = unlist(lapply(1:8, function(x) rep(names(folders)[[x]], ncol(dat[[x]])))),
                   row.names  = colnames(mat))
meta$sample <- factor(meta$sample_no)
## THE ORGAN MAPPING - this single line is what assigns tags to compartments
levels(meta$sample) <- c(rep("Spl", 2), rep("mLN", 2), rep("LP", 2), rep("EL", 2))
cat("\ncells per tag:\n"); print(table(meta$sample_no))
cat("\ncells per compartment:\n"); print(table(meta$sample))

genes <- data.frame(
  id              = sapply(strsplit(rownames(dat[[1]]), "\\|"), "[[", 2),
  loc             = sapply(strsplit(rownames(dat[[1]]), "\\|"), "[[", 3),
  gene_short_name = sapply(strsplit(rownames(dat[[1]]), "\\|"), "[[", 1),
  row.names       = make.unique(sapply(strsplit(rownames(dat[[1]]), "\\|"), "[[", 1)))
rownames(genes) <- genes$id
rownames(mat)   <- rownames(genes)

seu <- CreateSeuratObject(mat, meta.data = meta)
seu <- seu[, seu$sample %in% c("LP", "EL")]
cat("\ncells kept (LP + EL only):", ncol(seu), "\n")
cat("  LP:", sum(seu$sample == "LP"), "  EL:", sum(seu$sample == "EL"), "\n")
cat("genes:", nrow(seu), "\n")
cat("NOTE: the Rmd applies NO mitochondrial or count-based QC filter.\n\n")

seu <- NormalizeData(seu, normalization.method = "LogNormalize", scale.factor = 10000)
seu <- FindVariableFeatures(seu, nfeatures = 3000)
seu <- ScaleData(seu)
seu <- RunPCA(seu, features = VariableFeatures(object = seu))
seu <- FindNeighbors(seu, dims = 1:20)
seu <- FindClusters(seu, resolution = 1)
seu <- RunUMAP(seu, dims = 1:20)
cat("clusters found:", nlevels(factor(seu$seurat_clusters)),
    " (not used by the published panels - both group by sample)\n\n")

rownames(seu) <- genes$gene_short_name

## --- the panels -------------------------------------------------------------
pdf(file.path(FIG, "figS3A_UMAP_by_sample.pdf"), width = 7, height = 5)
print(DimPlot(seu, group.by = "sample")); dev.off()
png(file.path(FIG, "figS3A_UMAP_by_sample.png"), width = 1400, height = 1050, res = 150)
print(DimPlot(seu, group.by = "sample")); dev.off()

dot_genes <- c("Tbx21","Rorc","Ifng","Il17a","Nkg7","Gzmb","Gzma","Fasl","Tnfsf10")
pdf(file.path(FIG, "figS3B_dotplot.pdf"), width = 7, height = 6)
print(scCustomize::DotPlot_scCustom(seu, features = rev(dot_genes), group.by = "sample", flip_axes = TRUE)); dev.off()
png(file.path(FIG, "figS3B_dotplot.png"), width = 1400, height = 1200, res = 150)
print(scCustomize::DotPlot_scCustom(seu, features = rev(dot_genes), group.by = "sample", flip_axes = TRUE)); dev.off()

featg <- c("Nkg7","Prf1","Gzmb","Gzma","Gzmk","Gzmm","Ifng","Il17a","Il17f",
           "Tnfsf10","Fasl","Tbx21","Rorc")
pdf(file.path(FIG, "figS3C_featureplots.pdf"), width = 6, height = 6)
for (g in featg) if (g %in% rownames(seu)) print(FeaturePlot_scCustom(seu, g))
dev.off()

## --- the numbers a comparison needs -----------------------------------------
cat("=== DotPlot values (fig. S3B), for direct comparison ===\n")
dp <- scCustomize::DotPlot_scCustom(seu, features = rev(dot_genes), group.by = "sample", flip_axes = TRUE)
d  <- dp$data
cat(sprintf("%-10s %-4s %10s %10s\n", "gene", "grp", "avg.scaled", "pct.exp"))
for (i in seq_len(nrow(d)))
  cat(sprintf("%-10s %-4s %10.4f %10.2f\n", as.character(d$features.plot[i]),
              as.character(d$id[i]), d$avg.exp.scaled[i], d$pct.exp[i]))
write.csv(d, file.path(OUT, "figS3B_dotplot_values.csv"), row.names = FALSE)

saveRDS(seu, file.path(OUT, "exp80_figS3.RDS"))
cat("\nsessionInfo:\n"); print(sessionInfo())
cat("\n=== DONE ===\n")
sink()
