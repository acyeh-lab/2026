#!/bin/bash
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
