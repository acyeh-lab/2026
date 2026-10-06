#!/usr/bin/env Rscript
## ---------------------------------------------------------------------------
## install_packages.R - build the R environment this deposit needs.
##
##     export ADY3001_LIB=~/ady3001_Rlib
##     Rscript 03_environment/install_packages.R
##
## Reads ../r_packages.yml and installs each package AT THE RECORDED VERSION
## into $ADY3001_LIB (default <package>/Rlib). Nothing is installed into your
## system or user library, and nothing already correct is reinstalled.
##
## Dependencies ARE installed (the lab pin script passes dependencies = FALSE,
## which is only safe when a complete validated library already exists).
##
## Expect this to take 30-90 minutes from cold. It needs a compiler toolchain;
## on a cluster load a module first, e.g.
##     module load R/4.4.0-gfbf-2023b
##
## R 4.4.x is expected. R shares libraries by MAJOR.MINOR, so 4.4.0 / 4.4.1 /
## 4.4.2 interoperate; 4.5.x would need everything rebuilt.
## ---------------------------------------------------------------------------

args <- commandArgs(trailingOnly = TRUE)
here <- local({
  a <- commandArgs(FALSE); f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f)) dirname(normalizePath(f[1])) else normalizePath(getwd())
})
PKG <- dirname(here)
LIB <- Sys.getenv("ADY3001_LIB", file.path(PKG, "Rlib"))
LIB <- strsplit(LIB, ":", fixed = TRUE)[[1]][1]      # install into the first
dir.create(LIB, recursive = TRUE, showWarnings = FALSE)
if (!dir.exists(LIB)) stop("cannot create library: ", LIB)
.libPaths(c(LIB, .libPaths()))

cat("target library :", LIB, "\n")
cat("R              :", R.version.string, "\n\n")
if (getRversion() < "4.4.0" || getRversion() >= "4.5.0")
  cat("WARNING: this deposit was validated on R 4.4.x; you are on ",
      as.character(getRversion()), ".\n\n", sep = "")

## --- parse r_packages.yml (flat "  name: \"version\"" under source sections) --
yml <- file.path(PKG, "r_packages.yml")
if (!file.exists(yml)) stop("cannot find ", yml)
lines <- readLines(yml)
section <- NA_character_
cran <- bioc <- character(); gh <- list(); ghver <- character()
for (i in seq_along(lines)) {
  l <- lines[i]
  if (grepl("^(cran|bioconductor|github|base|unresolved):\\s*$", l)) {
    section <- sub(":.*$", "", l); next
  }
  if (is.na(section)) next
  m <- regmatches(l, regexec('^\\s{2}([A-Za-z][A-Za-z0-9._]*):\\s*"([^"]+)"', l))[[1]]
  if (length(m) == 3) {
    if (section == "cran") cran[m[2]] <- m[3]
    else if (section == "bioconductor") bioc[m[2]] <- m[3]
    next
  }
  nm <- regmatches(l, regexec('^\\s{2}- name:\\s*(\\S+)', l))[[1]]
  if (length(nm) == 2 && section == "github") {
    v <- regmatches(lines[i + 1], regexec('version:\\s*"([^"]+)"', lines[i + 1]))[[1]]
    r <- regmatches(lines[i + 2], regexec('repo:\\s*(\\S+)', lines[i + 2]))[[1]]
    if (length(r) == 2) { gh[[nm[2]]] <- r[2]; ghver[nm[2]] <- if (length(v) == 2) v[2] else NA }
  }
}
cat(sprintf("r_packages.yml: %d CRAN, %d Bioconductor, %d GitHub\n\n",
            length(cran), length(bioc), length(gh)))

have <- function(p, want) {
  d <- tryCatch(as.character(utils::packageVersion(p, lib.loc = .libPaths())),
                error = function(e) NA_character_)
  !is.na(d) && d == want
}

if (!requireNamespace("remotes", quietly = TRUE))
  install.packages("remotes", lib = LIB, repos = "https://cloud.r-project.org")
if (!requireNamespace("BiocManager", quietly = TRUE))
  install.packages("BiocManager", lib = LIB, repos = "https://cloud.r-project.org")

failed <- character()
step <- function(p, ver, how) {
  if (have(p, ver)) { cat(sprintf("  have   %-22s %s\n", p, ver)); return(invisible()) }
  cat(sprintf("  build  %-22s %s\n", p, ver))
  ok <- tryCatch({ how(); have(p, ver) }, error = function(e) {
    cat("         ERROR: ", conditionMessage(e), "\n", sep = ""); FALSE })
  if (!ok) failed[[length(failed) + 1L]] <<- p
}

## Seurat MUST precede scCustomize, which byte-compiles against it; otherwise
## the build reaches for whatever Seurat is already installed.
first <- intersect(c("Rcpp", "rlang", "vctrs", "SeuratObject", "Seurat"), names(cran))
order_cran <- c(first, setdiff(names(cran), first))

cat("--- CRAN ---\n")
for (p in order_cran)
  step(p, cran[[p]], function()
    remotes::install_version(p, version = cran[[p]], lib = LIB,
                             repos = "https://cloud.r-project.org",
                             upgrade = "never", dependencies = TRUE))

cat("--- Bioconductor ---\n")
for (p in names(bioc))
  step(p, bioc[[p]], function()
    BiocManager::install(p, lib = LIB, update = FALSE, ask = FALSE))

cat("--- GitHub ---\n")
for (p in names(gh))
  step(p, ifelse(is.na(ghver[[p]]), "", ghver[[p]]), function()
    remotes::install_github(gh[[p]], lib = LIB, upgrade = "never"))

cat("\n--- functional test ---\n")
bad <- character()
for (p in c("Seurat", "ggplot2", "scCustomize", "ggpubr", "dplyr", "Matrix",
            "data.table", "patchwork")) {
  ok <- suppressWarnings(suppressMessages(
    require(p, character.only = TRUE, quietly = TRUE, lib.loc = .libPaths())))
  cat(sprintf("  %-14s %s\n", p, if (ok) "loads" else "FAILS TO LOAD"))
  if (!ok) bad <- c(bad, p)
}
if (length(failed) || length(bad)) {
  cat("\n### PROBLEMS\n")
  if (length(failed)) cat("  did not install: ", paste(unique(failed), collapse = ", "), "\n")
  if (length(bad))    cat("  will not load  : ", paste(bad, collapse = ", "), "\n")
  cat("\nThe figure scripts will not run until these are resolved.\n")
  quit(status = 1)
}
cat("\n### ENVIRONMENT READY\n")
cat("Now:  export ADY3001_LIB=", LIB, "\n", sep = "")
