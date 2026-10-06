#!/usr/bin/env python3
"""
Build the Zenodo code deposit for Koyama et al., ady3001 (Science Immunology).

    module load Python/3.11.5-GCCcore-13.2.0
    python3 build_zenodo_package.py [--out DIR]

Re-runnable and deterministic: it wipes and rebuilds the package directory from
the working copies in Rebuild/ and from the original Rmds, so the package is
never hand-edited and can never drift from its sources.

WHAT THIS PACKAGE IS FOR
------------------------
GEO (GSE348009) takes the data. It does not take figure-generation code, and the
GitHub repository the Methods cite is incomplete (see 01_original_code/
KNOWN_ISSUES.md). This deposit is therefore the only complete record of how the
seven scRNA-seq figures were produced.

THE ONE TRANSFORMATION APPLIED TO THE SCRIPTS
---------------------------------------------
The working copies hardcode /fh/fast/hill_g/... , which is fatal for a deposit
that someone else downloads. Only the path-resolution header of each script is
rewritten, to read three environment variables via common/config.R. Every line
of analysis below that header is copied byte-for-byte. The full diff is shipped
in the package at 05_verification/path_rewrite.diff so the claim is checkable.

Every replacement below is ASSERTED. A substitution that silently matches
nothing would produce a package that looks built and is broken.
"""
import argparse, datetime, hashlib, os, re, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import package_docs as docs

ROOT = "/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024"
REB = os.path.join(ROOT, "Rebuild")
MARILYN = "/fh/fast/hill_g/Rhapsody/Marilyn"
VERSION = "1.0.0"
TODAY = "2026-09-21"

LAB_CLEAN_ROOM = os.path.join(REB, "geo", "clean_room", "unpacked")


def sub1(text, pattern, repl, what, flags=0):
    """Substitute exactly once, or die. A no-op match is a silent broken build."""
    new, n = re.subn(pattern, repl, text, flags=flags)
    if n != 1:
        raise SystemExit(f"FATAL: '{what}' matched {n} times, expected exactly 1")
    return new


# --------------------------------------------------------------------------
# the bootstrap that replaces the hardcoded ROOT/REB block
# --------------------------------------------------------------------------
BOOTSTRAP = '''## --- path resolution (Zenodo package) ---------------------------------------
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
'''

CONFIG_R = r'''## ---------------------------------------------------------------------------
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
## ADY3001_LAB_ROOT is only for re-running inside the Hill Lab allocation, where
## --source original (the matrices as delivered by BD's Seven Bridges) and
## --source rebuilt (matrices regenerated from FASTQ) are available. A reader of
## this deposit wants --source deposit, which is the default.
## ---------------------------------------------------------------------------

if (!exists("PKG")) stop("config.R must be sourced after PKG is set")

ADY_DATA <- Sys.getenv("ADY3001_DATA", file.path(PKG, "data"))
## Default output is the CURRENT directory, never inside the package - writing
## results into the Zenodo payload would corrupt the archived artefact.
OUT_ROOT <- Sys.getenv("ADY3001_OUT", file.path(getwd(), "ady3001_output"))

## Lab-only sources. Absent elsewhere, and the scripts say so rather than
## failing later with a confusing "file not found". The default below is the
## Hill Lab allocation and is deliberately the ONLY absolute path in this
## package; --source deposit never touches it.
LAB_ROOT <- Sys.getenv("ADY3001_LAB_ROOT", "/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024")
ROOT <- LAB_ROOT
REB  <- file.path(LAB_ROOT, "Rebuild")

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

source(file.path(PKG, "02_figure_scripts", "common", "load_bd.R"))

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
'''


def transform_main_script(src, exp, has_data_switch=True):
    """Rewrite only the path header of an Exp160/Exp649 figure script.

    has_data_switch is False for 02_fig7_figS11.R, which takes no matrices at
    all - its input is the Seurat object 01_figS10_qc.R wrote, so it carries no
    DEPOSIT_ROOT to rewrite.
    """
    t = open(src, encoding="utf-8").read()

    # 1. hardcoded ROOT/REB/source(load_bd.R)  ->  bootstrap + config.R
    t = sub1(
        t,
        r'ROOT\s*<-\s*"[^"]*BD_Rhapsody_Motoko_ISC_2024"\n'
        r'REB\s*<-\s*file\.path\(ROOT, "Rebuild"\)\n'
        r'source\(file\.path\(REB, "common/scripts/R/load_bd\.R"\)\)\n',
        lambda m: BOOTSTRAP,
        f"{exp}: ROOT/REB/load_bd block",
    )

    # 2. the deposit default -> ADY3001_DATA
    if has_data_switch:
        t = sub1(
            t,
            r'Sys\.getenv\("DEPOSIT_ROOT",\s*"[^"]*"\)',
            'Sys.getenv("ADY3001_DATA", file.path(PKG, "data"))',
            f"{exp}: DEPOSIT_ROOT default",
        )

    # 3. outputs go under OUT_ROOT, not back into the lab Rebuild tree
    t = sub1(
        t,
        r'OUT\s*<-\s*file\.path\(REB,\s*"(Exp\d+)",\s*"02_r_rebuild",\s*\n?\s*(paste0\([^)]*\))\)',
        lambda m: f'OUT <- file.path(OUT_ROOT, "{m.group(1)}", {m.group(2)})',
        f"{exp}: OUT root",
    )

    # 4. AUDIT B3. The default source must be "deposit", not "original".
    #    "original" is the lab copy of the BD output; outside the Hill Lab it
    #    does not exist, so a reader who follows the README (which never passes
    #    --source) had $ADY3001_DATA silently ignored and got an obscure
    #    "found 0" error from the loader. Worse, inside the lab the run would
    #    SUCCEED off the lab copy, hiding the bug on the only machine that
    #    could notice it.
    if has_data_switch:
        t = sub1(
            t,
            r'SOURCE\s*<-\s*getopt\("--source",\s*"original"\)',
            'SOURCE <- getopt("--source", "deposit")',
            f"{exp}: SOURCE default -> deposit",
        )
    else:
        t = sub1(
            t,
            r'SOURCE\s*<-\s*getopt\("--source",\s*"original"\);',
            'SOURCE <- getopt("--source", "deposit");',
            f"{exp}: SOURCE default -> deposit (no data switch)",
        )

    # 5. AUDIT B3. Actually CALL the guard config.R defines. It was written to
    #    turn a missing data directory into an actionable message and was dead
    #    code.
    if has_data_switch:
        t = sub1(
            t,
            r'(\n\s*stop\("--source must be original, rebuilt or deposit"\)\)\n)',
            lambda m: m.group(1) + 'ady_check_data(DATA, SOURCE)\n',
            f"{exp}: call ady_check_data",
        )

    # 6. AUDIT M6. DEPOSIT_ROOT was renamed ADY3001_DATA in this rewrite; the
    #    comment telling the reader to set it was left behind.
    t = t.replace(
        "## Set DEPOSIT_ROOT to point somewhere else (e.g. a real GEO download).",
        "## Set $ADY3001_DATA to point at your unpacked GEO download.")

    # 7. AUDIT M6/usage. The Usage line omitted the source that is now default.
    t = t.replace("[--source original|rebuilt]",
                  "[--source deposit|original|rebuilt]")
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "Zenodo"))
    a = ap.parse_args()

    pkgname = f"ady3001-scseq-code-v{VERSION}"
    pkg = os.path.join(a.out, pkgname)
    if os.path.exists(pkg):
        shutil.rmtree(pkg)
    os.makedirs(pkg)

    def D(*p):
        d = os.path.join(pkg, *p)
        os.makedirs(d, exist_ok=True)
        return d

    def put(rel, text, mode=0o644):
        p = os.path.join(pkg, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.chmod(p, mode)
        return p

    def copy(src, rel, mode=None):
        p = os.path.join(pkg, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        if not os.path.exists(src):
            raise SystemExit(f"FATAL: source missing: {src}")
        shutil.copyfile(src, p)          # plain copy: never cp -p under hill_g
        os.chmod(p, mode if mode else 0o644)
        return p

    put(".ady3001_root", f"ady3001 scRNA-seq code deposit v{VERSION}\n")

    # ---------------------------------------------------------------- 01 original
    D("01_original_code")
    copy(os.path.join(ROOT, "Exp160/rmd/Exp160_Final.Rmd"),
         "01_original_code/Exp160_Final.Rmd")
    copy(os.path.join(ROOT, "Exp160/Exp160_AYEH_241108_FINAL.Rmd"),
         "01_original_code/Exp160_AYEH_241108_FINAL.Rmd")
    copy(os.path.join(ROOT, "Exp649/rmd/Exp649_Final.Rmd"),
         "01_original_code/Exp649_Final.Rmd")
    copy(os.path.join(ROOT, "Exp649/rmd/Exp649_AYEH_241104_FINAL.Rmd"),
         "01_original_code/Exp649_AYEH_241104_FINAL.Rmd")
    copy(os.path.join(MARILYN, "rmd/241221_Marilyn.Rmd"),
         "01_original_code/241221_Marilyn.Rmd")
    copy(os.path.join(MARILYN, "rmd/241221_Marilyn.html"),
         "01_original_code/241221_Marilyn.html")

    # ---------------------------------------------------------------- 02 scripts
    D("02_figure_scripts/common")
    put("02_figure_scripts/common/config.R", CONFIG_R)

    # load_bd.R carries a hardcoded lab library path of its own. It is harmless
    # in the lab (guarded by dir.exists) but it has no business in a deposit,
    # and config.R already places ADY3001_LIB first. Strip it.
    t = open(os.path.join(REB, "common/scripts/R/load_bd.R"),
             encoding="utf-8").read()
    t = sub1(
        t,
        r'## ggpubr and ArchR are absent.*?\nlocal\(\{\n'
        r'  lib <- "[^"]*"\n'
        r'  if \(dir\.exists\(lib\)\) \.libPaths\(c\(lib, \.libPaths\(\)\)\)\n'
        r'\}\)\n',
        '## The library search path is set by config.R from $ADY3001_LIB before\n'
        '## this file is sourced. ggpubr and ArchR are not in a stock R library;\n'
        '## see 03_environment/README.md.\n',
        "load_bd.R: hardcoded Rlib path",
        flags=re.S,
    )
    put("02_figure_scripts/common/load_bd.R", t)

    pairs = [
        (os.path.join(REB, "Exp160/02_r_rebuild/01_fig4_figS6.R"),
         "02_figure_scripts/Exp160/01_fig4_figS6.R", True),
        (os.path.join(REB, "Exp160/02_r_rebuild/02_figS7.R"),
         "02_figure_scripts/Exp160/02_figS7.R", True),
        (os.path.join(REB, "Exp649/02_r_rebuild/01_figS10_qc.R"),
         "02_figure_scripts/Exp649/01_figS10_qc.R", True),
        (os.path.join(REB, "Exp649/02_r_rebuild/02_fig7_figS11.R"),
         "02_figure_scripts/Exp649/02_fig7_figS11.R", False),
    ]
    for src, rel, has_switch in pairs:
        put(rel, transform_main_script(src, os.path.basename(src), has_switch),
            mode=0o755)

    # 02_fig7_figS11.R additionally reads the object 01_figS10_qc.R wrote
    p = os.path.join(pkg, "02_figure_scripts/Exp649/02_fig7_figS11.R")
    t = open(p, encoding="utf-8").read()
    t = sub1(
        t,
        r'IN\s*<-\s*file\.path\(REB,\s*"Exp649",\s*"02_r_rebuild",\s*\n\s*'
        r'(paste0\("outS10_", SOURCE, "_", WHICH\)),\s*"cds",\s*"all_cells_processed\.RDS"\)',
        lambda m: ('IN  <- file.path(OUT_ROOT, "Exp649",\n                 '
                   f'{m.group(1)}, "cds", "all_cells_processed.RDS")'),
        "Exp649 02: IN path",
    )
    open(p, "w", encoding="utf-8").write(t)

    # ---- Exp80
    t = open(os.path.join(REB, "Exp80/02_r_rebuild/02_figS3_from_deposit.R"),
             encoding="utf-8").read()
    t = sub1(t, r'CR\s*<-\s*Sys\.getenv\("DEPOSIT_ROOT",\s*\n\s*"[^"]*"\)',
             'CR   <- Sys.getenv("ADY3001_DATA", file.path(PKG, "data"))',
             "Exp80 deposit: CR")
    t = sub1(t, r'REB\s*<-\s*"[^"]*"\nOUT\s*<-\s*file\.path\(REB, "Exp80", "02_r_rebuild", "out_figS3_deposit"\)',
             'OUT  <- file.path(OUT_ROOT, "Exp80", "out_figS3_deposit")',
             "Exp80 deposit: OUT")
    t = sub1(t, r'(suppressPackageStartupMessages\(\{)', BOOTSTRAP + r"\n\1",
             "Exp80 deposit: bootstrap")
    # AUDIT B5. A THIRD lab-only path, reachable on the --source deposit route.
    # The working copy defined REB locally; after the rewrite REB resolves via
    # config.R to the Hill Lab allocation, so this comparison silently degraded
    # to "reference not found" for every outside reader - while README.md cited
    # its result (4.4e-16) as evidence. verify_package.sh could not see it
    # because the path is built from a variable, not a literal.
    t = sub1(
        t,
        r'ref_f <- file\.path\(REB, "Exp80", "02_r_rebuild", "out_figS3",\s*\n?\s*"figS3B_dotplot_values\.csv"\)',
        'ref_f <- Sys.getenv("ADY3001_FIGS3_REF",\n'
        '                    file.path(OUT_ROOT, "Exp80", "out_figS3",\n'
        '                              "figS3B_dotplot_values.csv"))',
        "Exp80 deposit: ref_f (audit B5)",
    )
    t = t.replace(
        'cat("   reference not found:", ref_f, "\\n")',
        'cat("   reference not found:", ref_f, "\\n")\n'
        '  cat("   This comparison needs the EIGHT-tag run, which uses data that\\n")\n'
        '  cat("   is NOT on GEO (SampleTag01-04). It is expected to be absent\\n")\n'
        '  cat("   outside the Hill Lab. Routes A and B above are the\\n")\n'
        '  cat("   reader-reproducible check; this one is supplementary.\\n")')
    put("02_figure_scripts/Exp80/02_figS3_from_deposit.R", t, mode=0o755)

    t = open(os.path.join(REB, "Exp80/02_r_rebuild/01_figS3.R"),
             encoding="utf-8").read()
    # AUDIT M5. 02_figS7.R's header still said the Fig 4 / S6 analysis used
    # percent.mt < 25 "as written in the Rmd". That is the single most important
    # correction this deposit carries, and the header contradicted it.
    p7 = os.path.join(pkg, "02_figure_scripts/Exp160/02_figS7.R")
    t7 = open(p7, encoding="utf-8").read()
    t7 = sub1(
        t7,
        r'## Note the QC threshold differs from the Fig 4 / S6 analysis: percent\.mt < 40\n'
        r'## here, percent\.mt < 25 there, and resolution 0\.1 here against 0\.15 there\.\n'
        r'## Both are as written in the Rmd; they are not harmonised\.\n',
        "## QC threshold: percent.mt < 40, and resolution 0.1 here against 0.15\n"
        "## in the Fig 4 / S6 analysis.\n"
        "##\n"
        "## NOTE: the Rmd read \"< 25\" for the Fig 4 / S6 analysis until it was\n"
        "## corrected on 2026-10-06. That value was STALE - the published Fig 4\n"
        "## object holds 8,032 cells with a percent.mt maximum of 39.994, and 25\n"
        "## yields 6,412. BOTH analyses used 40, and the Rmd now says so. See\n"
        "## 01_original_code/KNOWN_ISSUES.md. The resolutions (0.1 / 0.15)\n"
        "## genuinely do differ and are correct as stated.\n",
        "figS7: stale percent.mt=25 header (audit M5)",
    )
    open(p7, "w", encoding="utf-8").write(t7)

    t = sub1(t, r'DATA_DIR\s*<-\s*"[^"]*"',
             'DATA_DIR <- Sys.getenv("ADY3001_EXP80_FULL", "/fh/fast/hill_g/Rhapsody/Marilyn/data")  # lab-only: the 8-tag data is not on GEO',
             "Exp80 full: DATA_DIR")
    t = sub1(t, r'OUT\s*<-\s*"[^"]*out_figS3"',
             'OUT <- file.path(OUT_ROOT, "Exp80", "out_figS3")',
             "Exp80 full: OUT")
    t = sub1(t, r'(suppressPackageStartupMessages\(\{)', BOOTSTRAP + r"\n\1",
             "Exp80 full: bootstrap")
    put("02_figure_scripts/Exp80/01_figS3_all8tags_LAB_ONLY.R", t, mode=0o755)

    # ---------------------------------------------------------------- 03 env
    D("03_environment")
    # The portable installer a reader actually uses (audit B2).
    put("03_environment/install_packages.R", docs.INSTALL_R, mode=0o755)
    # The lab scripts are kept as the record of what was done HERE, but they
    # hardcode an #SBATCH --output path, the target library and /home/ayeh/R,
    # so they cannot run anywhere else. Filed under lab_reference/ and headed
    # with a warning so nobody mistakes them for the installer.
    warn = ("# ===================================================================\n"
            "# LAB REFERENCE ONLY - THIS SCRIPT WILL NOT RUN OUTSIDE THE HILL LAB\n"
            "# ALLOCATION AT FRED HUTCH.\n"
            "#\n"
            "# It hardcodes an #SBATCH --output directory, the target library and\n"
            "# /home/ayeh/R/..., and it passes dependencies = FALSE, which is only\n"
            "# safe when a complete validated library already exists.\n"
            "#\n"
            "# To build the environment, use:  03_environment/install_packages.R\n"
            "#\n"
            "# This file is deposited because it is the record of how the pinned\n"
            "# library was actually built for the published runs.\n"
            "# ===================================================================\n")
    for f in ("install_r_pin.sh", "install_ggpubr.sh", "install_r_deps.sh"):
        src = os.path.join(REB, "common/scripts", f)
        body = open(src, encoding="utf-8").read()
        # keep the shebang first so the file is still a valid script
        if body.startswith("#!"):
            nl = body.index("\n") + 1
            body = body[:nl] + warn + body[nl:]
        else:
            body = warn + body
        put(f"03_environment/lab_reference/{f}", body, mode=0o755)
    for src, rel in [
        (os.path.join(REB, "Exp160/02_r_rebuild/out_deposit_RSEC/sessionInfo.txt"),
         "03_environment/sessionInfo_Exp160_Fig4_S6.txt"),
        (os.path.join(REB, "Exp160/02_r_rebuild/outS7_deposit_RSEC/sessionInfo.txt"),
         "03_environment/sessionInfo_Exp160_FigS7.txt"),
        (os.path.join(REB, "Exp649/02_r_rebuild/outS10_deposit_RSEC/sessionInfo.txt"),
         "03_environment/sessionInfo_Exp649_FigS10.txt"),
        (os.path.join(REB, "Exp649/02_r_rebuild/outFig7_deposit_RSEC/sessionInfo.txt"),
         "03_environment/sessionInfo_Exp649_Fig7_S11.txt"),
    ]:
        copy(src, rel)

    # AUDIT M4. There was no Exp80 environment record in the package, although
    # both READMEs tabulated one. Two now ship, and they are different things.
    #
    # (a) the deposit run's own sessionInfo, from the report that script writes
    rep = os.path.join(REB, "Exp80/02_r_rebuild/out_figS3_deposit",
                       "figS3_deposit_report.txt")
    body = open(rep, encoding="utf-8", errors="replace").read()
    i = body.find("sessionInfo:")
    put("03_environment/sessionInfo_Exp80_FigS3_depositrun.txt",
        "# Exp80 fig. S3, THIS deposit's run.\n"
        "# R 4.4.0 / Seurat 5.1.0 - deliberately NOT the original environment;\n"
        "# see sessionInfo_Exp80_FigS3_ORIGINAL.txt and the note in README.md.\n\n"
        + (body[i:] if i >= 0 else body))

    # (b) the ORIGINAL Exp80 environment. This is the ONLY original sessionInfo
    #     that exists for any published analysis in this paper - neither final
    #     Rmd was ever knitted. It survives only inside the rendered HTML.
    hp = os.path.join(MARILYN, "rmd/241221_Marilyn.html")
    ht = open(hp, encoding="utf-8", errors="replace").read()
    j = ht.find("R version 4.3.2")
    if j < 0:
        raise SystemExit("FATAL: Exp80 original sessionInfo not found in " + hp)
    import html as _h
    txt = _h.unescape(re.sub(r"<[^>]+>", "", ht[j:j + 6000]))
    txt = txt.split("</code>")[0]
    keep = []
    for line in txt.splitlines():
        keep.append(line)
        if len(keep) > 120:
            break
    put("03_environment/sessionInfo_Exp80_FigS3_ORIGINAL.txt",
        "# THE ORIGINAL Exp80 / fig. S3 environment: R 4.3.2, Seurat 5.0.0,\n"
        "# macOS arm64. Extracted from the rendered 241221_Marilyn.html, which\n"
        "# is the only place it survives.\n"
        "#\n"
        "# This is the ONLY original sessionInfo that exists for ANY published\n"
        "# analysis in this paper - neither final Rmd was ever knitted. See\n"
        "# 03_environment/README.md.\n\n" + "\n".join(keep) + "\n")

    # ---------------------------------------------------------------- 04 bd
    D("04_bd_pipeline")
    for src, rel, mode in [
        (os.path.join(REB, "common/scripts/run_bd_pipeline.sh"),
         "04_bd_pipeline/run_bd_pipeline.sh", 0o755),
        (os.path.join(REB, "common/scripts/make_ymls.py"),
         "04_bd_pipeline/make_ymls.py", 0o644),
        (os.path.join(REB, "common/scripts/rebuild_abseq_reference.py"),
         "04_bd_pipeline/rebuild_abseq_reference.py", 0o644),
        (os.path.join(REB, "common/scripts/patch_cwl_nullsafe_ram.py"),
         "04_bd_pipeline/patch_cwl_nullsafe_ram.py", 0o644),
        (os.path.join(REB, "common/scripts/fetch_bd_assets.sh"),
         "04_bd_pipeline/fetch_bd_assets.sh", 0o755),
        (os.path.join(REB, "common/scripts/make_cwl_env.sh"),
         "04_bd_pipeline/make_cwl_env.sh", 0o755),
        (os.path.join(REB, "common/scripts/compare_matrices.py"),
         "04_bd_pipeline/compare_matrices.py", 0o644),
    ]:
        copy(src, rel, mode=mode)
    for d in ("v1.9.1", "v1.10.1"):
        s = os.path.join(REB, "common/scripts/cwl", d)
        if os.path.isdir(s):
            for f in sorted(os.listdir(s)):
                if os.path.isfile(os.path.join(s, f)):
                    copy(os.path.join(s, f), f"04_bd_pipeline/cwl/{d}/{f}")
    ab = os.path.join(REB, "common/abseq")
    if os.path.isdir(ab):
        for f in sorted(os.listdir(ab)):
            if f.endswith((".fasta", ".txt")) and "allReference" not in f:
                copy(os.path.join(ab, f), f"04_bd_pipeline/abseq/{f}")

    # ---------------------------------------------------------------- 05 verify
    D("05_verification")
    copy(os.path.join(REB, "common/scripts/R/verify_deposit_vs_published.R"),
         "05_verification/verify_deposit_vs_published.R")
    copy(os.path.join(REB, "common/scripts/compare_figures.py"),
         "05_verification/compare_figures.py")

    # ---- the actual diffs, so the "path-only" claim is checkable, not asserted
    SRCMAP = [
        (os.path.join(REB, "Exp160/02_r_rebuild/01_fig4_figS6.R"),
         "02_figure_scripts/Exp160/01_fig4_figS6.R"),
        (os.path.join(REB, "Exp160/02_r_rebuild/02_figS7.R"),
         "02_figure_scripts/Exp160/02_figS7.R"),
        (os.path.join(REB, "Exp649/02_r_rebuild/01_figS10_qc.R"),
         "02_figure_scripts/Exp649/01_figS10_qc.R"),
        (os.path.join(REB, "Exp649/02_r_rebuild/02_fig7_figS11.R"),
         "02_figure_scripts/Exp649/02_fig7_figS11.R"),
        (os.path.join(REB, "Exp80/02_r_rebuild/02_figS3_from_deposit.R"),
         "02_figure_scripts/Exp80/02_figS3_from_deposit.R"),
        (os.path.join(REB, "Exp80/02_r_rebuild/01_figS3.R"),
         "02_figure_scripts/Exp80/01_figS3_all8tags_LAB_ONLY.R"),
        (os.path.join(REB, "common/scripts/R/load_bd.R"),
         "02_figure_scripts/common/load_bd.R"),
    ]
    dif = ["# Complete diff of every packaged script against the lab working",
           "# copy that produced the published figures.",
           "#",
           "# Read this to check the claim that only path resolution changed.",
           "# Left  (---) = the lab working copy under Rebuild/",
           "# Right (+++) = this package",
           f"# Generated {TODAY} by Rebuild/zenodo/build_zenodo_package.py", "", ""]
    for src, rel in SRCMAP:
        r = subprocess.run(["diff", "-u", src, os.path.join(pkg, rel)],
                           capture_output=True, text=True)
        dif.append("=" * 74)
        dif.append(f"=== {rel}")
        dif.append("=" * 74)
        dif.append(r.stdout if r.stdout else "(identical)")
    put("05_verification/path_rewrite.diff", "\n".join(dif))

    # ---------------------------------------------------------------- docs
    put("README.md", docs.README)
    put("LICENSE", docs.LICENSE_MIT)
    put("CITATION.cff", docs.CITATION_CFF)
    put("EXPECTED_RESULTS.tsv", docs.EXPECTED_RESULTS)
    put("01_original_code/KNOWN_ISSUES.md", docs.KNOWN_ISSUES)
    put("03_environment/README.md", docs.ENV_README)
    put("04_bd_pipeline/README.md", docs.BD_README)
    put("tools/unpack_geo_download.sh", docs.UNPACK_SH, mode=0o755)
    put("run_all.sh", docs.RUN_ALL_SH, mode=0o755)
    put("verify_package.sh", docs.VERIFY_SH, mode=0o755)

    # environment YAML, measured from sessionInfo + installed DESCRIPTIONs
    import glob
    sess = {}
    sfiles = sorted(glob.glob(os.path.join(
        REB, "Exp*/02_r_rebuild/out*deposit*/sessionInfo.txt")))
    if len(sfiles) != 4:
        raise SystemExit(f"FATAL: expected 4 deposit sessionInfo files, found {len(sfiles)}")
    pat = re.compile(r'([A-Za-z][A-Za-z0-9._]*)_(\d[0-9A-Za-z.\-]*)')
    for f in sfiles:
        for m in pat.finditer(open(f, encoding="utf-8").read()):
            sess.setdefault(m.group(1), set()).add(m.group(2))
    envyml, rpkgs = docs.build_environment_yaml(REB, sess)
    put("environment.yml", envyml)
    put("r_packages.yml", rpkgs)
    unres = rpkgs.count("NOT RESOLVED")
    print(f"environment.yml + r_packages.yml: {len(sess)} packages"
          + (" (some unresolved)" if unres else ""))

    # figure map, MEASURED from the verified deposit runs
    rows, counts = docs.build_figure_map(REB)
    put("FIGURE_MAP.tsv", "\n".join("\t".join(r) for r in rows) + "\n")
    total = sum(counts.values())
    print(f"figure map: {total} panels across {len(counts)} scripts")
    for k, v in counts.items():
        print(f"    {k:34s} {v:3d}")
    if total != 124:
        raise SystemExit(f"FATAL: expected 124 panels, measured {total}")

    # ---------------------------------------------------------------- manifest
    lines = []
    for dirpath, dirnames, filenames in os.walk(pkg):
        dirnames.sort()
        for f in sorted(filenames):
            if f == "MANIFEST.sha256":
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, pkg)
            h = hashlib.sha256(open(full, "rb").read()).hexdigest()
            lines.append(f"{h}  {rel}")
    put("MANIFEST.sha256", "\n".join(lines) + "\n")

    nbytes = sum(os.path.getsize(os.path.join(dp, f))
                 for dp, _, fs in os.walk(pkg) for f in fs)
    print(f"built: {pkg}")
    print(f"       {len(lines) + 1} files, {nbytes / 1024:.0f} KiB")
    return pkg


if __name__ == "__main__":
    main()
