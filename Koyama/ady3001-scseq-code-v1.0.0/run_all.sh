#!/bin/bash
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
