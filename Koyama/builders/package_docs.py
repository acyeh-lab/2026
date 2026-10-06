#!/usr/bin/env python3
"""
Documentation, tooling and manifest for the ady3001 Zenodo package.

Imported by build_zenodo_package.py. Kept separate so the prose can be edited
without touching the code that rewrites the R scripts.

The figure map is MEASURED from the deposit-run output directories, never typed
out by hand - a hand-typed map drifts from the scripts the first time a panel is
renamed.
"""
import os, re

VERSION = "1.0.0"
TODAY = "2026-09-21"
GSE = "GSE348009"

# deposit-run output dirs that the figure map is measured from
RUNS = [
    ("Exp160", "01_fig4_figS6.R",   "Exp160/02_r_rebuild/out_deposit_RSEC"),
    ("Exp160", "02_figS7.R",        "Exp160/02_r_rebuild/outS7_deposit_RSEC"),
    ("Exp649", "01_figS10_qc.R",    "Exp649/02_r_rebuild/outS10_deposit_RSEC"),
    ("Exp649", "02_fig7_figS11.R",  "Exp649/02_r_rebuild/outFig7_deposit_RSEC"),
    ("Exp80",  "02_figS3_from_deposit.R", "Exp80/02_r_rebuild/out_figS3_deposit"),
]


def build_figure_map(REB):
    """Enumerate every panel each script writes, tagged with its manuscript figure."""
    rows = [("manuscript_figure", "panel_file", "experiment", "script", "run_directory")]
    counts = {}
    for exp, script, rel in RUNS:
        d = os.path.join(REB, rel, "figs")
        if not os.path.isdir(d):
            raise SystemExit(f"FATAL: figure-map source missing: {d}")
        n = 0
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith((".pdf", ".png")):
                continue
            m = re.match(r"\[(Fig[^\]]+)\]", f)
            if m:
                fig = m.group(1)
            elif f.startswith("figS3"):
                fig = "FigS3" + (f[5] if len(f) > 5 and f[5].isalpha() else "")
            elif f.startswith("[GSEA]"):
                fig = "Fig7C/Fig7F/FigS11C (GSEA)"
            elif f.startswith("[QC]"):
                fig = "(QC, not a manuscript panel)"
            else:
                fig = "(QC, not a manuscript panel)"
            rows.append((fig, f, exp, script, rel))
            n += 1
        counts[script] = n
    return rows, counts


LICENSE_MIT = """MIT License

Copyright (c) 2026 Albert C. Yeh, Motoko Koyama, Geoffrey R. Hill,
Fred Hutchinson Cancer Center

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

CITATION_CFF = f"""cff-version: 1.2.0
message: "If you use this software, please cite both the article and this archive."
title: "Analysis code for Koyama et al., IFN-gamma-driven MHC class II expression by intestinal epithelial cells dictates local cytolytic Th1 differentiation and intestinal stem cell loss"
version: "{VERSION}"
date-released: "{TODAY}"
license: MIT
abstract: >-
  Complete single-cell RNA-sequencing analysis code for Koyama et al.
  (Science Immunology, ady3001). Regenerates Figures 4, 7, S3, S6, S7, S10 and
  S11 from the matrices deposited in NCBI GEO under accession {GSE}, and
  optionally from the raw FASTQ via the version-pinned BD Rhapsody pipeline.
authors:
  - family-names: Yeh
    given-names: Albert C.
    affiliation: "Fred Hutchinson Cancer Center"
  - family-names: Koyama
    given-names: Motoko
    affiliation: "Fred Hutchinson Cancer Center"
  - family-names: Hill
    given-names: Geoffrey R.
    affiliation: "Fred Hutchinson Cancer Center"
keywords:
  - single-cell RNA sequencing
  - graft-versus-host disease
  - intestinal stem cells
  - MHC class II
  - interferon gamma
  - BD Rhapsody
identifiers:
  - type: other
    value: "{GSE}"
    description: "NCBI GEO accession for the underlying data"
"""

UNPACK_SH = r'''#!/bin/bash
# ---------------------------------------------------------------------------
# unpack_geo_download.sh  <download_dir>  <dest_dir>
#
# A GEO supplementary-file download is FLAT. These scripts expect one directory
# per cartridge, and for Exp80 one directory per sample tag whose name ends
# "_mm". Without this step a reader's first run finds zero files and looks like
# a broken deposit.
#
#   1. download the supplementary files of GSE348009 (all six GSM records plus
#      the series-level file) into one directory
#   2. ./unpack_geo_download.sh ~/Downloads/GSE348009 ~/ady3001_data
#   3. export ADY3001_DATA=~/ady3001_data
#
# Symlinks are used, so nothing is duplicated. Pass -c to copy instead.
# ---------------------------------------------------------------------------
set -uo pipefail
COPY=0
[ "${1:-}" = "-c" ] && { COPY=1; shift; }
SRC="${1:?usage: unpack_geo_download.sh [-c] <download_dir> <dest_dir>}"
DST="${2:?usage: unpack_geo_download.sh [-c] <download_dir> <dest_dir>}"
SRC=$(cd "$SRC" && pwd) || { echo "no such directory: $1"; exit 1; }
mkdir -p "$DST"; DST=$(cd "$DST" && pwd)

missing=0
place() {   # place <subdir> <filename>
  local sub="$1" f="$2"
  mkdir -p "$DST/$sub"
  # GEO prefixes SAMPLE supplementary files with the GSM id and SERIES-level
  # ones with the GSE id. MM_Immune_Response_amplicons.fasta is series-level,
  # so a GSM-only pattern reports it missing on a real download and aborts.
  # -type f alone also misses a download directory made of symlinks.
  local hit
  hit=$(find "$SRC" -maxdepth 2 \( -type f -o -type l \) \
          \( -name "$f" -o -name "GSM*_$f" -o -name "GSE*_$f" \) | sort | head -1)
  if [ -z "$hit" ]; then
    echo "  MISSING  $f"; missing=$((missing+1)); return
  fi
  if [ "$COPY" = 1 ]; then cp -- "$hit" "$DST/$sub/$f"; else ln -sf "$hit" "$DST/$sub/$f"; fi
  echo "  ok       $sub/$f"
}

echo "=== Exp160 (GSM10065191-3) ==="
for c in 1 2 3; do
  place "Exp160/data/cartridge$c" "cartridge${c}_RSEC_MolsPerCell.csv"
  place "Exp160/data/cartridge$c" "cartridge${c}_Metrics_Summary.csv"
  place "Exp160/data/cartridge$c" "cartridge${c}_RSEC_MolsPerCell_Unfiltered.csv.gz"
done

echo "=== Exp649 (GSM10065194-5) ==="
for c in 1 2; do
  place "Exp649/data/Cart$c" "Cart${c}_RSEC_MolsPerCell.csv"
  place "Exp649/data/Cart$c" "Cart${c}_DBEC_MolsPerCell.csv"
  place "Exp649/data/Cart$c" "Cart${c}_Metrics_Summary.csv"
  place "Exp649/data/Cart$c" "Cart${c}_RSEC_MolsPerCell_Unfiltered.csv.gz"
done

echo "=== Exp80 (GSM10065196) ==="
# NOTE the directory name must end "_mm" - the Sample_Tag_Calls file spells the
# tag "SampleTag05_mm", not "SampleTag05", and the loader globs on that suffix.
for t in 05 06 07 08; do
  place "Exp80/data/mRNA-ST-GCTACGCT_SampleTag${t}_mm" \
        "mRNA-ST-GCTACGCT_SampleTag${t}_mm_RSEC_MolsPerCell.csv"
done
for f in Combined_mRNA-ST-GCTACGCT_RSEC_MolsPerCell.csv \
         Combined_mRNA-ST-GCTACGCT_DBEC_MolsPerCell.csv \
         mRNA-ST-GCTACGCT_Sample_Tag_Calls.csv \
         mRNA-ST-GCTACGCT_Metrics_Summary.csv \
         mRNA-ST-GCTACGCT_Sample_Tag_Metrics.csv \
         mRNA-ST-GCTACGCT_RSEC_MolsPerCell_Unfiltered.csv.gz; do
  place "Exp80/data" "$f"
done
place "Exp80/data" "MM_Immune_Response_amplicons.fasta"

echo
echo "broken symlinks (must be none):"
find "$DST" -xtype l -print | sed 's/^/  BROKEN /'
echo
if [ "$missing" -gt 0 ]; then
  echo "### $missing file(s) MISSING - the download is incomplete."
  exit 1
fi
echo "### OK - now:  export ADY3001_DATA=$DST"
'''

RUN_ALL_SH = r'''#!/bin/bash
# ---------------------------------------------------------------------------
# run_all.sh - regenerate every published scRNA-seq panel, in order.
#
#   export ADY3001_DATA=/path/to/unpacked/GEO/download
#   export ADY3001_OUT=/path/for/results          # optional
#   ./run_all.sh
#
# ORDER MATTERS in exactly one place: Exp649/02_fig7_figS11.R reads the Seurat
# object written by Exp649/01_figS10_qc.R. Everything else is independent.
#
# Runtime is roughly 20-60 min per script on 8 cores; Exp649/02 is the longest
# because of the GSEA permutations. Peak memory ~60 GB for Exp649/01.
# ---------------------------------------------------------------------------
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$HERE"

: "${ADY3001_DATA:?set ADY3001_DATA to the unpacked GEO download (see tools/unpack_geo_download.sh)}"
# Default output goes to the CURRENT directory, never inside the package -
# writing results into the Zenodo payload would corrupt the thing you archived.
export ADY3001_OUT="${ADY3001_OUT:-$PWD/ady3001_output}"
case "$ADY3001_OUT" in
  "$HERE"/*) echo "NOTE: ADY3001_OUT is inside the package directory." ;;
esac
mkdir -p "$ADY3001_OUT"

echo "package : $HERE"
echo "data    : $ADY3001_DATA"
echo "output  : $ADY3001_OUT"
echo "R       : $(Rscript -e 'cat(R.version.string)' 2>/dev/null)"
echo

fail=0
run() {
  echo "=========================================================="
  echo "=== $1"
  echo "=========================================================="
  if Rscript "$1" --source deposit; then
    echo "--- OK   $1"
  else
    echo "--- FAIL $1"; fail=$((fail+1))
  fi
  echo
}

run 02_figure_scripts/Exp160/01_fig4_figS6.R        # Fig 4,  Fig S6
run 02_figure_scripts/Exp160/02_figS7.R             # Fig S7
run 02_figure_scripts/Exp649/01_figS10_qc.R         # Fig S10   (must precede the next)
run 02_figure_scripts/Exp649/02_fig7_figS11.R       # Fig 7,  Fig S11
echo "=== 02_figure_scripts/Exp80/02_figS3_from_deposit.R"
Rscript 02_figure_scripts/Exp80/02_figS3_from_deposit.R || fail=$((fail+1))

echo
echo "=========================================================="
# Count BOTH extensions. The Exp80 script writes figS3A and figS3B as PDF *and*
# PNG, so a PDF-only count reports 122 where FIGURE_MAP.tsv and README say 124.
npdf=$(find "$ADY3001_OUT" -name '*.pdf' | wc -l)
npng=$(find "$ADY3001_OUT" -name '*.png' | wc -l)
printf 'panels written: %s   (%s pdf + %s png; expected 124 = 122 + 2)\n' \
       "$((npdf + npng))" "$npdf" "$npng"
nempty=$(find "$ADY3001_OUT" \( -name '*.pdf' -o -name '*.png' \) -size 0 | wc -l)
printf 'empty panels  : %s   (must be 0)\n' "$nempty"
[ "$nempty" -gt 0 ] && fail=$((fail+1))
echo "failures: $fail"
[ "$fail" -eq 0 ] && echo "### ALL SCRIPTS COMPLETED" || echo "### $fail SCRIPT(S) FAILED"
exit "$fail"
'''

VERIFY_SH = r'''#!/bin/bash
# ---------------------------------------------------------------------------
# verify_package.sh - checks that do NOT need the data or a working R.
#
#   1. every file in MANIFEST.sha256 is present and hashes correctly
#   2. no absolute /fh/fast path survives in any script except the two places
#      that are documented lab-only fallbacks
#   3. every R script parses
#   4. the expected panel count is recorded for each script
#
# Run this first after downloading. It takes seconds.
# ---------------------------------------------------------------------------
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$HERE"
fail=0

echo "=== 1. checksums ==="
if command -v sha256sum >/dev/null; then
  if sha256sum -c MANIFEST.sha256 --quiet; then
    echo "  all files match MANIFEST.sha256"
  else
    echo "  CHECKSUM FAILURE"; fail=$((fail+1))
  fi
else
  echo "  sha256sum not found - skipped"
fi

echo
echo "=== 2. hardcoded lab paths in 02_figure_scripts/ ==="
# Two are expected and documented:
#   config.R            ADY3001_LAB_ROOT default (only used by --source original)
#   01_figS3_all8tags   ADY3001_EXP80_FULL default (data not on GEO)
# NOTE this is a LITERAL-string check. A lab path reached through a variable
# (e.g. file.path(REB, ...)) is invisible to it. One such case existed and was
# fixed; if you add code, do not rely on this check alone.
hits=$(grep -rn '/fh/fast/' 02_figure_scripts/ \
        | grep -v 'ADY3001_LAB_ROOT' \
        | grep -v 'ADY3001_EXP80_FULL' \
        | grep -v '^\S*:[0-9]*:##' || true)
if [ -z "$hits" ]; then
  echo "  no literal lab path outside the two documented fallbacks"
else
  echo "$hits" | sed 's/^/  UNEXPECTED /'; fail=$((fail+1))
fi

echo
echo "=== 2b. lab paths reached indirectly through REB/ROOT ==="
# The point of this check is a REB/ROOT reference OUTSIDE the documented
# --source original|rebuilt switch arms. One such line existed (the Exp80
# fig. S3 reference comparison) and check 2 could not see it, because the path
# is built from a variable rather than written as a literal.
# The switch arms themselves ARE the lab-only modes and are expected.
ind=$(grep -rn 'file\.path(REB\|file\.path(ROOT\|file\.path(LAB_ROOT' 02_figure_scripts/ \
        | grep -v '^\S*:[0-9]*:##' \
        | grep -vE ':[0-9]+:\s*(original|rebuilt)\s*=' \
        | grep -v 'common/config.R:.*REB  <- file.path(LAB_ROOT' || true)
if [ -z "$ind" ]; then
  echo "  none"
else
  echo "$ind" | sed 's/^/  INDIRECT /'; fail=$((fail+1))
fi

echo
echo "=== 3. every R script parses ==="
if command -v Rscript >/dev/null; then
  while IFS= read -r f; do
    if Rscript -e "invisible(parse('$f'))" >/dev/null 2>&1; then
      echo "  ok     $f"
    else
      echo "  PARSE FAIL $f"; fail=$((fail+1))
    fi
  done < <(find 02_figure_scripts -name '*.R' | sort)
else
  echo "  Rscript not found - skipped"
fi

echo
echo "=== 4. internal consistency ==="
# Check 4 used to be `cat EXPECTED_RESULTS.tsv`, which could never fail.
# It now cross-checks the two tables against each other.
fm_total=$(tail -n +2 FIGURE_MAP.tsv | wc -l)
er_total=$(tail -n +2 EXPECTED_RESULTS.tsv | awk -F'\t' '{s+=$6} END{print s+0}')
printf '  FIGURE_MAP.tsv rows      : %s\n' "$fm_total"
printf '  EXPECTED_RESULTS panels  : %s\n' "$er_total"
if [ "$fm_total" = "$er_total" ] && [ "$fm_total" = "124" ]; then
  echo "  consistent, and both equal the documented 124"
else
  echo "  MISMATCH - FIGURE_MAP and EXPECTED_RESULTS disagree, or != 124"
  fail=$((fail+1))
fi
# every script named in EXPECTED_RESULTS must exist
while IFS=$'\t' read -r scr rest; do
  [ "$scr" = script ] && continue
  [ -z "$scr" ] && continue
  if [ -f "02_figure_scripts/$scr" ]; then
    echo "  ok     02_figure_scripts/$scr"
  else
    echo "  MISSING SCRIPT 02_figure_scripts/$scr"; fail=$((fail+1))
  fi
done < EXPECTED_RESULTS.tsv
# the manifest must cover every file actually present
nfiles=$(find . -type f ! -name MANIFEST.sha256 | wc -l)
nman=$(wc -l < MANIFEST.sha256)
printf '  files on disk / in manifest : %s / %s\n' "$nfiles" "$nman"
[ "$nfiles" = "$nman" ] || { echo "  MANIFEST does not cover every file"; fail=$((fail+1)); }

echo
echo "=== 5. expected results ==="
sed 's/^/  /' EXPECTED_RESULTS.tsv

echo
[ "$fail" -eq 0 ] && echo "### PACKAGE OK" || echo "### $fail PROBLEM(S)"
exit "$fail"
'''


EXPECTED_RESULTS = """script\tmanuscript_figures\tcells_loaded\tcells_final\tclusters\tpanels\tnote
Exp160/01_fig4_figS6.R\tFig 4B-D, Fig S6A-E\t15288\t8032\t7\t40\tQC filter only (percent.mt < 40)
Exp160/02_figS7.R\tFig S7B-E\t23841\t7478\t6\t26\tQC filter only (percent.mt < 40)
Exp649/01_figS10_qc.R\tFig S10A-D\t30391\t9135\t12\t14\tQC filter gives 10363; 9135 is after AbSeq de-multiplexing (965 multiplets, 263 no-tag)
Exp649/02_fig7_figS11.R\tFig 7B-F, Fig S11A-C\t9135\t6828\t9\t39\tISC subset of the 9135
Exp80/02_figS3_from_deposit.R\tFig S3A-C\t4544\t4544\tn/a (grouped by sample)\t5\t1334+1600+871+739; no QC filter
"""

KNOWN_ISSUES = r"""# Known issues in the original R Markdown

These files are the **historical record**: the code as it stood when the
published figures were made. **One value was corrected** - see item 1 - and
everything else is deposited as it was, defects included, because a reader
comparing the paper to the code needs to see what was actually run.
**They will not knit from a clean session.** Use
`../02_figure_scripts/` for anything you intend to execute.

Each defect below was found by running the code, not by reading it.

---

## 1. `percent.mt` corrected from 25 to 40 (line 157) - CHANGED 2026-10-06

The Fig 4 / S6 filter in `Exp160_Final.Rmd` **now reads `percent.mt < 40`**.
Until 2026-10-06 it read `25`. That was a stale edit, not the threshold that
produced the figures: 25 keeps **6,412 cells**, whereas the object the published
figure was made from, `241108v2_processed.RDS`, holds **8,032 cells in 7
clusters** with a `percent.mt` maximum of 39.994 - and the Rmd's own inline
comment on that very line has always read "This gives us 8,032 samples".

**40 is the threshold that was actually used**, the same as Fig S7, S10 and S11.
Confirmed five independent ways:

- every object the figures are made from maxes near 40. (One object in the
  same folder, `241108_processed.RDS`, does max at 24.97 with 6,412 cells and 6
  clusters - that is the SUPERSEDED first pass at 25, written the same day.
  Neither Rmd ever wrote it: both save and read `241108v2`. It is the exception
  that proves which object is which, not a counter-example.)
- all four rebuild analyses reproduce the published objects at 40
- re-running the original Rmd at 25 gives 6,412 cells, not the 8,032 the Rmd's
  own inline comment claims
- the three other filter calls in the same file (lines 623, 827 and 1182) have
  always read 40, with comments giving 2,782 / 10,812 / 7,478 cells that match
  their published objects exactly. The file disagreed only with itself, on this
  one line.
- the first author confirms that 40 is what was run

The Rmd's YAML is dated 2025-08-14 while the object it reads was written
2024-11-11, so the `25` was introduced roughly nine months *after* the figures
were made. The same stale value stood in `Exp160_AYEH_241108_FINAL.Rmd`, which
saves and reads that same `241108v2` object, and was corrected there too.

**The difference is not cosmetic**, which is why it was corrected rather than
merely annotated. 40 keeps 20.2% more cells than 25 (8,032 against 6,412) and
yields the published **7** clusters, where re-running at 25 gives 8. The extra
cells are not debris - their median complexity (1,425 genes / 4,348 UMIs) is
*higher* than the retained set (1,234 / 3,304) - and they concentrate into a
distinct high-mitochondrial island that largely disappears at 25.

> The manuscript Methods were corrected to **40% for both** the IEC and the ISC
> analyses.

## 2. `DefaultAssay(seu_sub) <- "RNA"` precedes the creation of `seu_sub` (line 154)

Line 154 sets the default assay on `seu_sub`; line 157 creates it. On a clean
run this errors immediately. It only ever worked because `seu_sub` was left over
in an interactive session.

## 3. `test0_1` is never assigned (`Exp160_Final.Rmd`, volcano for Fig S7E)

The volcano data frame is built as

    volcano_0_2 <- data.frame(cbind(rownames(test0_2),
                                    test0_2$p_val_adj < 0.05,
                                    test0_2$avg_log2FC,
                                    test0_1$p_val))        # <- test0_1

`test0_1` appears nowhere in the Exp160 corpus, so this raises
`object 'test0_1' not found`. Every other column comes from `test0_2`
(cluster 0 vs cluster 2); the packaged script takes the p-value column from
`test0_2` as well.

## 4. `order_cells(cds)` is interactive (lines 478 and 501)

Called with no arguments, monocle3's `order_cells` opens a Shiny window and
blocks forever in a non-interactive run. The Fig S6B legend states the stem-cell
cluster was used as the root node, so the packaged script selects that root
programmatically.

## 5. Knitting these files in place is DESTRUCTIVE

`Exp160_Final.Rmd` writes `saveRDS(..., "241108v2_processed.RDS")` straight into
the analysis directory, and about forty `pdf()` calls overwrite the published
figure PDFs. `Exp649_Final.Rmd` overwrites two more objects.

Running `Exp160_Final.Rmd` unmodified would overwrite the published 8,032-cell
object with a **wrong** 6,412-cell one, because of defect 1.

**Never knit these in a directory you care about.** Redirect the output
directories first.

---

## What is NOT wrong

- **The stated resolutions are correct.** In every saved object
  `seurat_clusters` is byte-identical to the `RNA_snn_res.*` column the Rmd
  names.
- **The seeds are correct.** Seurat's per-function seed defaults
  (`FindClusters(random.seed = 0)`, `RunPCA`/`RunUMAP(seed.use = 42)`,
  `AddModuleScore(seed = 1)`) are already fixed and the Rmds never override
  them. Do **not** "improve" this by passing `set.seed(1234)` into those calls -
  at resolution 0.15 it gives 8 communities where the published Fig 4 object has
  7.

---

## Relationship to the GitHub repository cited in the Methods

The Methods cite `https://github.com/acyeh-lab/2024/tree/main/Koyama/scseq`.
As of 2026-09-21 that directory holds three files and is **incomplete**:

| | on GitHub | here |
|---|---|---|
| `Exp160_Final.Rmd` | 486 lines, **7 chunks** | 1,551 lines, **17 chunks** |
| `Exp649_Final.Rmd` | 829 lines | 829 lines (identical but for a path typo) |
| `241221_Marilyn.Rmd` (Exp80, Fig S3) | **absent** | present |

The public `Exp160_Final.Rmd` is the pre-revision version. Missing from it:

- every `add Cart 3 ...` chunk - i.e. **all of Figure S7**
- `Lgr4 and Fgfbp1 - New ISC model` - **Figure S6C**

The public `Exp649_Final.Rmd` differs in two lines, both the same path error:
it says `scSeq_Analyses` where the directory is `scSeq_ST_Analyses`, so its
`setwd()` cannot succeed. Its `readme.txt` also uses the pre-revision figure
numbers ("Figure 3" and "Figure 6" for what are now Figures 4 and 7).

**This archive supersedes that repository.**
"""

ENV_README = r"""# Environment

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
"""

BD_README = r"""# Part 1 - FASTQ to expression matrices

**You do not need this to regenerate the figures.** GEO accession GSE348009
carries the expression matrices, and `02_figure_scripts/` starts from those.
This directory is here so the path from raw reads is auditable and re-runnable.

## Pinned versions - these are not interchangeable

| | Exp160 | Exp649 |
|---|---|---|
| BD pipeline | `bdgenomics/rhapsody:1.9.1` | `bdgenomics/rhapsody:1.10.1` |
| CWL | `rhapsody_wta_1.9.1.cwl` | `rhapsody_wta_1.10.1.cwl` |
| Genome | `GRCm38-PhiX-gencodevM19-20181206` | same |
| AbSeq panel | 4 pAbO | 7 pAbO (4 of them CD326 sample hashes) |

Both versions come from the experiments' own `Metrics_Summary.csv` headers.
Running a current BD release instead would not be a reproduction: v2.x changed
the reference format, the cell-calling algorithm and the outputs.

Exp80 used the **targeted** Immune Response panel on BD pipeline v1.8. The v1.8
targeted CWL is not published by BD and is not in the v1.8 container, so that
experiment's FASTQ-to-matrix step is **not version-matched reproducible**. The
deposited matrices are BD's original v1.8 output.

## The AbSeq references

The two AbSeq FASTAs named in the metrics headers were Seven Bridges inputs and
were not retained. Both are reconstructible exactly, and
`rebuild_abseq_reference.py` does it:

- the **panel** is the header row of each `*_RSEC_MolsPerCell.csv`, which lists
  every target in BD's four-field form
  (`CD326:G8.8-AMM2281|Epcam|AMM2281|pAbO`) - that string *is* the FASTA record
  name
- the **barcodes** come from BD's public cumulative reference,
  `s3://bd-rhapsody-public/AbSeq-references/BDAbSeq_allReference_<date>.fasta`,
  using the last release predating each experiment's own reference date
  (2020-08-20 for Exp160, 2022-03-17 for Exp649)

Cross-checked against the four printed BD data sheets; all four barcodes match.

The rebuilt FASTAs are in `abseq/`. They are **machine reconstructions**, and
are provided for re-running the pipeline only - they were deliberately not
deposited to GEO.

Still genuinely missing: Exp160's `combined_extra_seq.fasta` (supplemental
transgene sequences). No transgene name appears among Exp160's 21,907 gene
columns, so it contributed no detected target, but the Exp160 re-run is
therefore declared reference-incomplete rather than identical.

## How close the re-run came

Across all five cartridges, against BD's original Seven Bridges output:

- **feature sets and cell sets identical** in all five - same counts, zero
  entries on one side only
- total difference **0.0009-0.0013% of molecules**; median 1 molecule per
  differing cell; Pearson r = 1.000000
- for Exp160 every *gene* column is identical; the entire discrepancy sits in
  the four AbSeq channels

Re-running the figure scripts from those rebuilt matrices reproduces Fig 4, S6
and S7 identically. **Fig 7 / S11 does not reproduce from rebuilt matrices** -
Louvain at resolution 0.5 sits near a community boundary, so a 0.001% difference
in molecules renumbers the 12-cluster map and yields 7 ISC communities instead
of 9. The cell set is essentially unchanged (Jaccard 0.997). The script detects
this and refuses to claim a reproduction.

This is why **GEO carries the original matrices**, which reproduce every figure
exactly.

## Traps

- Singularity may be unable to loop-mount a `.sif` and will unpack ~6 GB per
  container start; `run_bd_pipeline.sh` builds one sandbox per job on local
  scratch and passes `--singularity-sandbox-path`.
- BD's v1.10.1 CWL evaluates a VDJ RAM hint over a null input when no VDJ
  library is present, and cwltool 3.2 refuses at the very end of an otherwise
  complete run. `patch_cwl_nullsafe_ram.py` writes a `.nullsafe.cwl`.
"""


README = r"""# Analysis code — Koyama et al., *Science Immunology* (ady3001)

**IFN-γ-driven MHC class II expression by intestinal epithelial cells dictates
local cytolytic Th1 differentiation and intestinal stem cell loss**

Version {VERSION} · {TODAY} · MIT licensed
Data: NCBI GEO **[{GSE}](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={GSE})**

---

## What this is

The complete single-cell RNA-sequencing analysis code for the paper. It
regenerates **seven figures** — every scRNA-seq panel in the manuscript — from
the expression matrices deposited in GEO.

| Figure | Panels | Experiment | Script |
|---|---|---|---|
| **Fig 4** | B–D | Exp160, ileal IEC, naïve + 24 h TBI WT | `Exp160/01_fig4_figS6.R` |
| **Fig S6** | A–E | same | `Exp160/01_fig4_figS6.R` |
| **Fig S7** | B–E | Exp160, 24 h TBI WT + MHC-II KO | `Exp160/02_figS7.R` |
| **Fig S10** | A–D | Exp649, ileal ISC, day 7 post-BMT | `Exp649/01_figS10_qc.R` |
| **Fig 7** | B–F | Exp649, Lgr5+ ISC subset | `Exp649/02_fig7_figS11.R` |
| **Fig S11** | A–C | same | `Exp649/02_fig7_figS11.R` |
| **Fig S3** | A–C | Exp80, Marilyn T cells, ileal EL vs LP | `Exp80/02_figS3_from_deposit.R` |

(Panel A of Figures 4, 7 and S7 is an experimental schema, not data. Fig S3D–F
are flow cytometry and cytotoxicity assays, not sequencing.)

`FIGURE_MAP.tsv` lists all **124** output panels individually.

---

## Quick start

```bash
# 1. check the package itself (seconds; needs neither data nor R packages)
./verify_package.sh

# 2. build the R environment  (30-90 min from cold; needs a compiler)
export ADY3001_LIB=~/ady3001_Rlib
Rscript 03_environment/install_packages.R

# 3. download the supplementary files of GSE348009 into one directory, then
#    rearrange them into the per-cartridge layout the scripts expect
./tools/unpack_geo_download.sh ~/Downloads/GSE348009 ~/ady3001_data
export ADY3001_DATA=~/ady3001_data

# 4. choose where results go (default: ./ady3001_output in the current dir)
export ADY3001_OUT=~/ady3001_output

# 5. regenerate every panel
./run_all.sh
```

**Step 2 is required.** The scripts need Seurat **5.1.0** specifically, and a
stock or current R library will not do &mdash; Seurat 5.5.x and ggplot2 4.x both
break this code (see `03_environment/README.md`).
`install_packages.R` reads `r_packages.yml` and installs the recorded versions
into `$ADY3001_LIB` without touching your system library.

Results land in `$ADY3001_OUT` (default `./output`). Compare against
`EXPECTED_RESULTS.tsv` — those cell and cluster counts are exact, not
approximate.

### Step 2 is not optional

A GEO download is **flat**. The scripts expect one directory per cartridge, and
for Exp80 one directory per sample tag whose name **ends `_mm`**. Skipping the
unpack step makes a correct deposit look empty.

---

## Layout

```
01_original_code/      the Rmds as they were when the figures were made,
                       unmodified — including the two that were never published
                       to GitHub. READ KNOWN_ISSUES.md BEFORE RUNNING THESE.
02_figure_scripts/     the runnable transcription. This is what you execute.
   common/             config.R (paths) + load_bd.R (matrix loader)
   Exp160/ Exp649/ Exp80/
03_environment/        install_packages.R (use this), sessionInfo of the
                       verified runs, and lab_reference/ (the lab's own pin
                       scripts — deposited as a record, NOT runnable elsewhere)
04_bd_pipeline/        optional: FASTQ → matrices, version-pinned BD Rhapsody.
                       LAB-PATHED: these were written for this cluster and are
                       deposited for auditability, not turnkey re-execution.
05_verification/       path_rewrite.diff (the full diff proving the scripts are
                       path-only changes) plus the scripts that proved the
                       deposit reproduces the paper. Also lab-pathed.
tools/                 unpack_geo_download.sh
FIGURE_MAP.tsv         every panel → the script that writes it
EXPECTED_RESULTS.tsv   exact cell / cluster / panel counts
MANIFEST.sha256        checksums for every file here
```

---

## Environment

| | Exp160 / Exp649 | Exp80 |
|---|---|---|
| R | **4.4.0** | **4.3.2** |
| Seurat | **5.1.0** | **5.0.0** |

The two experiments used different Seurat versions; this is not a typo.

**Pin your library.** On 2026-09-18 the library these packages lived in was
updated in place, Seurat went 5.1.0 → 5.5.1 and ggplot2 3.4.4 → 4.0.3, and the
analysis stopped running the same day. `03_environment/install_r_pin.sh`
reinstalls the validated versions into a private library; `config.R` puts it
first on `.libPaths()`. See `03_environment/README.md`.

---

## Two corrections to the published Methods

Both were found by running the code, and both are documented with evidence in
`01_original_code/KNOWN_ISSUES.md` and `03_environment/README.md`.

1. **The mitochondrial threshold is 40 %, not 25 % — now corrected in both
   places.** The Methods previously said "`percent.mt` < 25 % (IEC analysis) or
   < 40 % (ISC analysis)"; they now read 40 % for both, and line 157 of
   `Exp160_Final.Rmd` was corrected to match on 2026-10-06. Every published
   object — including the IEC ones — has a `percent.mt` maximum of ~40.
   Filtering at 25 keeps 6,412 cells; the published Fig 4 object holds
   **8,032 cells in 7 clusters**, and the corrected Rmd reproduces it
   cell-for-cell — identical barcodes, identical cluster sizes, 100.00 %
   agreement, `percent.mt` max 39.9936 against the published 39.9936 (verified
   2026-10-06). The difference is material: the 1,620 additional cells have
   *higher* median complexity than the retained set and form a distinct cluster.

2. **The R version is 4.4.0, not 4.0.3.** The Statistical analysis section says
   "R (ver. 4.0.3) for RNAseq data". All five published Seurat objects record
   `SeuratObject` 5.0.2 internally, which requires R ≥ 4.1.0 and was released in
   May 2024. R 4.0.3 (October 2020) cannot load these objects.

---

## Reproducibility evidence

Every script here was run against a **clean room** containing nothing but the 28
processed files actually deposited in GEO, md5-verified against the upload
manifest, with no other project file reachable:

| Figure | Cells | Clusters | Cluster sizes | Cell-for-cell agreement with the published object |
|---|---|---|---|---|
| Fig 4 / S6 | 8,032 | 7 | identical | **100.00 %** |
| Fig S7 | 7,478 | 6 | identical | **100.00 %** |
| Fig S10 | 9,135 | 12 | identical | **100.00 %** |
| Fig 7 / S11 | 6,828 | 9 | identical | **100.00 %** |

Fig S3 reproduces by **two independent routes** — the four deposited per-tag
matrices, and the deposited Combined matrix split by the deposited
`Sample_Tag_Calls.csv` — which give byte-identical matrices; the dot-plot values
agree with the full eight-tag run to 4.4 × 10⁻¹⁶.

124 panels written, none empty.

### Known limits, stated plainly

- **UMAP orientation is not reproducible, and does not need to be.** A UMAP is
  defined only up to rotation and reflection. The Fig S3A rebuild is
  horizontally mirrored relative to the published panel; the structure,
  groupings and all quantitative values are identical.
- **Figures 7 / S11 do not reproduce from matrices regenerated from FASTQ.**
  They reproduce exactly from the deposited matrices, which is what GEO carries.
  Louvain clustering at resolution 0.5 sits near a community boundary for this
  dataset, so the 0.001 % molecule-level difference introduced by re-running the
  BD pipeline renumbers the map and yields 7 ISC communities instead of 9. The
  cell set is essentially unchanged (Jaccard 0.997). The script detects this and
  refuses to claim a reproduction rather than quietly subsetting the wrong
  cells.
- **Exp80's FASTQ→matrix step is not version-matched.** BD never published the
  v1.8 targeted CWL and it is not in the v1.8 container. The deposited matrices
  are BD's original output.
- **Do not add seeds.** Seurat's per-function seed defaults are already fixed and
  the original code never overrode them. Passing `set.seed(1234)` into
  `FindClusters` gives 8 communities where the published Fig 4 object has 7.

---

## Relationship to the GitHub repository in the Methods

The Methods cite `github.com/acyeh-lab/2024/tree/main/Koyama/scseq`. That
directory is **incomplete**: its `Exp160_Final.Rmd` is the pre-revision version
missing all of Figure S7 and Figure S6C, and the Exp80 code was never pushed at
all. **This archive supersedes it.**

---

## Citation

Please cite the article and this archive. See `CITATION.cff`.
""".replace("{VERSION}", VERSION).replace("{TODAY}", TODAY).replace("{GSE}", GSE)


# ---------------------------------------------------------------------------
# environment YAML
#
# Built by READING each package's installed DESCRIPTION, so the version and the
# CRAN-vs-Bioconductor split are measured rather than assumed. A package whose
# DESCRIPTION carries a biocViews: field is a Bioconductor package; that is the
# field Bioconductor itself requires and is the reliable discriminator.
# ---------------------------------------------------------------------------
R_LIBS = [
    "/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild/common/Rlib_pin",
    "/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild/common/Rlib",
    "/home/ayeh/R/x86_64-pc-linux-gnu-library/4.4",
    # the R module's own library, which supplies base/recommended packages and
    # everything EasyBuild bundled with R 4.4.0. Without it ~20 packages look
    # unresolved when they are simply installed somewhere else.
    "/app/software/R/4.4.0-gfbf-2023b/lib/R/library",
]

# "Priority: base" packages ship with R itself and have no independent version;
# sessionInfo prints them at the R version. They are not installable separately
# and must not appear in a conda or remotes list.
BASE_PKGS = {"base", "compiler", "datasets", "grDevices", "graphics", "grid",
             "methods", "parallel", "splines", "stats", "stats4", "tcltk",
             "tools", "utils"}

# sessionInfo's "Platform: x86_64-pc-linux-gnu" line matches the <name>_<version>
# package pattern. It is not a package.
NOT_PACKAGES = {"x86"}

# The source of each package is READ from its DESCRIPTION, never assumed. An
# earlier hand-written list here classified scCustomize as GitHub-only; its
# DESCRIPTION says "Repository: CRAN", and sending a reader to GitHub for a
# CRAN package is exactly the kind of error this deposit exists to avoid.
#
# Discriminators, in precedence order:
#
#   RemoteType: github   -> installed from GitHub (RemoteUsername/RemoteRepo)
#   Repository: CRAN     -> CRAN
#   biocViews: present   -> Bioconductor
#
# RemoteType MUST outrank biocViews. presto, monocle3 and SeuratWrappers each
# carry a biocViews field AND were installed from GitHub, so testing biocViews
# first would send a reader to Bioconductor for packages that are not there.


def _describe(pkg):
    """Return (version, source, repo) for an installed package, read from its
    DESCRIPTION, or (None, None, None) if it is not installed anywhere."""
    for lib in R_LIBS:
        d = os.path.join(lib, pkg, "DESCRIPTION")
        if not os.path.exists(d):
            continue
        f = {}
        for line in open(d, encoding="utf-8", errors="replace"):
            m = re.match(r"^([A-Za-z][A-Za-z0-9]*):\s*(.*)$", line)
            if m:
                f.setdefault(m.group(1), m.group(2).strip())
        ver = f.get("Version")
        if not ver:
            continue
        if pkg in BASE_PKGS:
            return ver, "base", None
        if f.get("RemoteType") == "github":
            user, repo = f.get("RemoteUsername"), f.get("RemoteRepo")
            return ver, "github", (f"{user}/{repo}" if user and repo else None)
        if f.get("Repository") == "CRAN":
            return ver, "cran", None
        if "biocViews" in f:
            return ver, "bioconductor", None
        return ver, "cran", None
    return None, None, None


def build_environment_yaml(REB, sessioninfo_versions):
    """Emit (environment.yml, r_packages.yml) as strings."""
    resolved = {}
    for pkg, vers in sorted(sessioninfo_versions.items()):
        if pkg in NOT_PACKAGES:
            continue
        if pkg in BASE_PKGS:
            resolved[pkg] = (sorted(vers)[0], "base", None)
            continue
        ver, src, repo = _describe(pkg)
        if ver is None:
            ver, src, repo = sorted(vers)[0], "unresolved", None
        resolved[pkg] = (ver, src, repo)

    by = {"cran": [], "bioconductor": [], "github": [], "base": [],
          "unresolved": []}
    for p, (v, src, repo) in sorted(resolved.items()):
        by[src].append((p, v, repo))

    head = (
        "# ---------------------------------------------------------------------------\n"
        "# r_packages.yml - the exact R package versions that produced the published\n"
        "# figures of Koyama et al., Science Immunology (ady3001).\n"
        "#\n"
        f"# Generated {TODAY} from the sessionInfo of the verified deposit runs and the\n"
        "# DESCRIPTION file of every installed package. Nothing here is typed by hand.\n"
        "#\n"
        "# THIS IS A RECORD, NOT AN INSTALLER. It states what ran. Use\n"
        "# environment.yml or 03_environment/install_r_pin.sh to build an environment.\n"
        "#\n"
        "# The two experiments used DIFFERENT Seurat versions and this is not an error:\n"
        "#   Exp160 / Exp649 (Fig 4, 7, S6, S7, S10, S11) : R 4.4.0, Seurat 5.1.0\n"
        "#   Exp80           (Fig S3)                     : R 4.3.2, Seurat 5.0.0\n"
        "# The versions below are the Exp160/Exp649 environment, in which Fig S3 also\n"
        "# reproduces (a deliberate version-drift test; see README.md).\n"
        "# ---------------------------------------------------------------------------\n"
    )
    y = [head, "r_version: \"4.4.0\"", "bioconductor_release: \"3.19\"",
         "platform: \"x86_64-pc-linux-gnu\"", ""]
    y.append(f"# {len(resolved)} packages total")
    for src, label in (("cran", "CRAN"), ("bioconductor", "Bioconductor"),
                       ("github", "GitHub (not on CRAN or Bioconductor)"),
                       ("base", "base R - ships with R, not separately installable"),
                       ("unresolved", "NOT RESOLVED - version from sessionInfo only")):
        if not by[src]:
            continue
        y.append("")
        y.append(f"# --- {label} ({len(by[src])}) " + "-" * max(0, 50 - len(label)))
        y.append(f"{src}:")
        for p, v, repo in by[src]:
            if src == "github":
                y.append(f"  - name: {p}")
                y.append(f"    version: \"{v}\"")
                y.append(f"    repo: {repo or 'UNKNOWN - read its DESCRIPTION'}")
            else:
                y.append(f"  {p}: \"{v}\"")
    rpkgs = "\n".join(y) + "\n"

    # ---- conda environment.yml -------------------------------------------
    # conda-forge names CRAN packages r-<lowercase>; bioconda names
    # Bioconductor packages bioconductor-<lowercase>. GitHub-only packages have
    # no conda package and are listed as a remotes: block for renv/devtools.
    e = [
        "# ---------------------------------------------------------------------------",
        "# environment.yml - conda/mamba environment for the ady3001 figure scripts.",
        "#",
        f"# Generated {TODAY}. Versions are the ones that produced the published",
        "# figures; see r_packages.yml for the full measured record.",
        "#",
        "#     mamba env create -f environment.yml",
        "#     conda activate ady3001",
        "#",
        "# CAVEAT, read before relying on this: conda-forge and bioconda do not carry",
        "# every one of these versions for every platform, and five packages below are",
        "# GitHub-only and have no conda package at all - install those with the",
        "# remotes block underneath. The environment that is KNOWN to reproduce the",
        "# figures is the module-based one built by 03_environment/install_r_pin.sh;",
        "# this file is a portable approximation of it, offered for convenience.",
        "# ---------------------------------------------------------------------------",
        "name: ady3001",
        "channels:",
        "  - conda-forge",
        "  - bioconda",
        "  - nodefaults",
        "dependencies:",
        "  - r-base=4.4.0",
    ]
    for p, v, _ in by["cran"]:
        e.append(f"  - r-{p.lower()}={v}")
    for p, v, _ in by["bioconductor"]:
        e.append(f"  - bioconductor-{p.lower()}={v}")
    e += [
        "",
        "# Not available from conda. After creating the environment, run:",
        "#",
        "#     R -e 'install.packages(\"remotes\")'",
    ]
    for p, v, repo in by["github"]:
        e.append(f"#     R -e 'remotes::install_github(\"{repo}\")'   # {p} {v}")
    envyml = "\n".join(e) + "\n"
    return envyml, rpkgs


# ---------------------------------------------------------------------------
# AUDIT B2. The lab pin scripts hardcode an #SBATCH --output path, the target
# library and /home/ayeh/R/..., and install only 11 packages with
# dependencies = FALSE. They cannot build an environment anywhere else, and the
# README's Quick start never told the reader to build one at all - so a first
# ./run_all.sh died at library(Seurat).
#
# This installer is portable: it reads r_packages.yml (the measured record) and
# installs into $ADY3001_LIB. The lab scripts are kept, clearly marked, because
# they document what was actually done here.
# ---------------------------------------------------------------------------
INSTALL_R = r'''#!/usr/bin/env Rscript
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
'''
