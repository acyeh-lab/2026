## ---------------------------------------------------------------------------
## load_bd.R - shared loader for BD Rhapsody RSEC_MolsPerCell matrices
##
## This is a faithful transcription of the loading block that opens both
## Exp160_Final.Rmd and Exp649_Final.Rmd, with three changes, each of which is
## a fix to something that would stop a clean re-run, not a change of method:
##
##   1. Files are selected by NAME, not by position. The Rmds do
##        f <- list.files(...)[grep("RSEC_MolsPerCell", list.files(...))]
##        files <- f[c(2,4)]
##      which depends on the alphabetical position of *_RSEC_MolsPerCell.csv
##      among *_RSEC_MolsPerCell_Unfiltered.csv.gz etc. Add or remove a file in
##      the directory and it silently loads the wrong matrix. Here the filtered
##      per-cell matrix is matched explicitly.
##
##   2. The number of AbSeq (protein) rows is read from the file, not hardcoded.
##      The Rmds hardcode mat[1:4,] for Exp160 and mat[1:7,] for Exp649. That is
##      correct for these files - BD writes the |pAbO columns first - but it is
##      counted here from the header and checked against the expected number, so
##      a different panel cannot be split at the wrong row.
##
##   3. set.seed(1234) is set before each processing block, as the Rmd does, but
##      Seurat's own per-function seeds are LEFT AT THEIR DEFAULTS. This matters:
##      FindClusters(random.seed = 0), RunPCA/RunUMAP(seed.use = 42) and
##      AddModuleScore(seed = 1) are already fixed seeds, and the Rmds never
##      override them - so the published objects were produced with those values.
##      Passing 1234 to them instead is deterministic but produces a DIFFERENT
##      answer: at resolution 0.15 it gives 8 communities where the published
##      Fig 4 object has 7.
##
## Nothing about normalisation, filtering, clustering or embedding is changed.
## ---------------------------------------------------------------------------

## The library search path is set by config.R from $ADY3001_LIB before
## this file is sourced. ggpubr and ArchR are not in a stock R library;
## see 03_environment/README.md.

suppressPackageStartupMessages({
  library(Matrix)
  library(data.table)
  library(Seurat)
})

## Locate the filtered per-cell molecule matrix for one cartridge.
## `which` is "RSEC" or "DBEC".
bd_matrix_path <- function(dir, which = c("RSEC", "DBEC")) {
  which <- match.arg(which)
  f <- list.files(dir, full.names = TRUE)
  hit <- grep(paste0("_", which, "_MolsPerCell\\.csv$"), f, value = TRUE)
  if (length(hit) != 1L)
    stop(sprintf("expected exactly one *_%s_MolsPerCell.csv in %s, found %d",
                 which, dir, length(hit)))
  hit
}

## Number of AbSeq targets, counted from the file's own header line.
bd_n_pabo <- function(path) {
  con <- file(path, "r"); on.exit(close(con))
  repeat {
    line <- readLines(con, n = 1L)
    if (!length(line)) stop("no header in ", path)
    if (!startsWith(line, "#")) break
  }
  cols <- strsplit(line, ",", fixed = TRUE)[[1]]
  if (cols[1] != "Cell_Index") stop(path, ": first column is ", cols[1])
  sum(endsWith(cols, "|pAbO"))
}

## Read one or more cartridges into a single sparse matrix.
##   dirs      named character vector: name = cart prefix, value = directory
##   n_pabo    expected number of AbSeq rows (checked, not assumed)
bd_load <- function(dirs, which = "RSEC", n_pabo = NULL) {
  paths <- vapply(dirs, bd_matrix_path, character(1), which = which)
  k <- unique(vapply(paths, bd_n_pabo, integer(1)))
  if (length(k) != 1L)
    stop("cartridges disagree on AbSeq panel size: ", paste(k, collapse = ", "))
  if (!is.null(n_pabo) && k != n_pabo)
    stop(sprintf("expected %d AbSeq targets, file header says %d", n_pabo, k))
  message(sprintf("  %s: %d cartridge(s), %d AbSeq targets", which, length(paths), k))

  dat <- lapply(paths, function(p) {
    message("  reading ", basename(p))
    t(as.matrix(data.table::fread(p), rownames = 1))
  })

  rn <- Reduce(intersect, lapply(dat, rownames))
  rn <- vapply(strsplit(rn, "\\|"), `[[`, character(1), 1L)
  dat <- lapply(dat, function(m) {
    rownames(m) <- vapply(strsplit(rownames(m), "\\|"), `[[`, character(1), 1L)
    m[rn, , drop = FALSE]
  })
  for (i in seq_along(dat))
    colnames(dat[[i]]) <- paste0(names(dirs)[i], "_", colnames(dat[[i]]))

  mat <- Matrix(do.call(cbind, dat), sparse = TRUE)
  colnames(mat) <- make.unique(colnames(mat))
  list(rna = mat[(k + 1L):nrow(mat), , drop = FALSE],
       adt = mat[1L:k, , drop = FALSE],
       n_pabo = k)
}

## Build the Seurat object exactly as the Rmds do.
bd_seurat <- function(loaded) {
  seu <- CreateSeuratObject(counts = loaded$rna)
  seu[["ADT"]] <- CreateAssayObject(
    counts = loaded$adt[, match(colnames(loaded$adt), Cells(seu)), drop = FALSE])
  seu$cart <- vapply(strsplit(Cells(seu), "_"), `[[`, character(1), 1L)
  seu[["percent.mt"]] <- PercentageFeatureSet(seu, pattern = "^mt-")
  seu$logUMI  <- log10(seu$nCount_RNA)
  seu$log_RNA <- log10(seu$nCount_RNA)
  seu
}

## The standard LogNormalize -> 3000 HVG -> scale -> PCA(50) block.
bd_process <- function(seu, dims, resolution, seed = 1234) {
  set.seed(seed)          # as the Rmd does at the top of the chunk
  DefaultAssay(seu) <- "RNA"
  seu <- NormalizeData(seu, normalization.method = "LogNormalize", scale.factor = 10000)
  seu <- FindVariableFeatures(seu, selection.method = "vst", nfeatures = 3000)
  seu <- ScaleData(seu)
  # Seurat's own seed defaults are deliberate here - see the note at the top.
  seu <- RunPCA(seu, features = VariableFeatures(object = seu), npcs = 50)
  seu <- FindNeighbors(seu, dims = dims)
  seu <- FindClusters(seu, resolution = resolution)
  seu <- RunUMAP(seu, dims = dims)
  seu
}

## CLR normalisation of the protein assay, as in both Rmds.
bd_process_adt <- function(seu) {
  DefaultAssay(seu) <- "ADT"
  seu <- NormalizeData(seu, normalization.method = "CLR")
  seu <- ScaleData(seu)
  DefaultAssay(seu) <- "RNA"
  seu
}

## rna_cols in the Rmds is ArchR::paletteContinuous(n=8)[c(1:3,6:8)].
bd_rna_cols <- function() {
  if (!requireNamespace("ArchR", quietly = TRUE))
    stop("ArchR is not installed; it defines rna_cols (paletteContinuous). ",
         "Run common/scripts/install_r_deps.sh first - do not substitute another palette.")
  ArchR::paletteContinuous(n = 8)[c(1:3, 6:8)]
}

bd_clus_cols36 <- c(
  "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b",
  "#e377c2", "#7f7f7f", "#bcbd22", "#17becf", "#aec7e8", "#ffbb78",
  "#98df8a", "#ff9896", "#c5b0d5", "#c49c94", "#f7b6d2", "#c7c7c7",
  "#dbdb8d", "#9edae5", "#ad494a", "#8c6d31", "#e7ba52", "#17becf",
  "#1f78b4", "#33a02c", "#fb9a99", "#e31a1c", "#fdbf6f", "#cab2d6",
  "#6a3d9a", "#ff8c00", "#b15928", "#41ab5d", "#f03b20", "#807dba")

bd_theme <- function() {
  library(ggplot2)
  theme_bw(base_size = 14) +
    theme(panel.background   = element_rect(fill = "transparent", colour = NA),
          panel.grid.minor   = element_blank(),
          panel.grid.major   = element_blank(),
          legend.background  = element_rect(fill = "transparent"),
          legend.box.background = element_rect(fill = "transparent"),
          legend.key         = element_rect(fill = "transparent", colour = NA),
          plot.background    = element_rect(fill = "transparent", colour = NA))
}

## Record exactly what produced a result.
bd_session <- function(path) {
  writeLines(c(capture.output(sessionInfo()), "",
               paste("run at", format(Sys.time(), "%Y-%m-%d %H:%M:%S"))), path)
}
