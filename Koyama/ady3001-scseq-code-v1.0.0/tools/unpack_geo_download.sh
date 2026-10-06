#!/bin/bash
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
