## ---------------------------------------------------------------------------
## config.R - path resolution for the ady3001 figure scripts.
##
## Sourced by every script in 02_figure_scripts/. It defines the paths and then
## loads the shared BD matrix loader. It contains NO analysis.
##
## THREE ENVIRONMENT VARIABLES, all optional:
##
##   ADY3001_DATA  the unpacked GEO download.  Default: <package>/data
##                 Produce it with:  tools/unpack_geo_download.sh <download> <dest>
##                 This is what a reader outside the Hill Lab uses.
##
##   ADY3001_OUT   where results are written.  Default: ./ady3001_output in the
##                 CURRENT directory - deliberately not inside the package.
##
##   ADY3001_LIB   extra R libraries, placed FIRST on .libPaths(), in order.
##                 Colon-separated, like $PATH. Default: <package>/Rlib if it
##                 exists. Build it with 03_environment/install_packages.R -
##                 see 03_environment/README.md for why a pinned library is not
##                 optional here.
##
## There is no ADY3001_LAB_ROOT and no --source switch in this copy. Each .Rmd
## sets DATA directly, in a single editable line at the top of its first chunk.
## ---------------------------------------------------------------------------

if (!exists("PKG")) stop("config.R must be sourced after PKG is set")

ADY_DATA <- Sys.getenv("ADY3001_DATA", file.path(PKG, "data"))
## Default output is the CURRENT directory, never inside the package - writing
## results into the Zenodo payload would corrupt the archived artefact.
OUT_ROOT <- Sys.getenv("ADY3001_OUT", file.path(getwd(), "ady3001_output"))

## NOTE: this copy drops the LAB_ROOT / ROOT / REB definitions that the Zenodo
## package carries. They existed only for `--source original|rebuilt`, which the
## one-line-edit preamble in each .Rmd removes, so they are dead here - and they
## were the only absolute path in the code.

## The pinned library must come first. The home R library that originally held
## these packages was updated in place on 2026-09-18 and the analysis stopped
## running the same day; see 03_environment/README.md.
local({
  spec <- Sys.getenv("ADY3001_LIB", file.path(PKG, "Rlib"))
  libs <- Filter(dir.exists, strsplit(spec, ":", fixed = TRUE)[[1]])
  if (length(libs)) {
    .libPaths(c(libs, .libPaths()))
    message("ady3001: library path -> ", paste(libs, collapse = ", "))
  }
})

source(file.path(PKG, "common", "load_bd.R"))

## Fail early and clearly if the caller asked for a source that is not present.
ady_check_data <- function(path, source_name) {
  if (!dir.exists(path)) {
    stop(sprintf(paste0(
      "\n  data directory not found: %s\n",
      "  --source %s resolves to that path.\n",
      "  If you downloaded GSE348009, unpack it first:\n",
      "      tools/unpack_geo_download.sh <download_dir> <dest>\n",
      "      export ADY3001_DATA=<dest>\n"), path, source_name))
  }
  invisible(path)
}
