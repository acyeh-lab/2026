#!/bin/bash
#SBATCH --partition=campus-new
#SBATCH --job-name=pkgtest
#SBATCH --cpus-per-task=8
#SBATCH --mem=180G
#SBATCH --time=12:00:00
#SBATCH --output=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild/zenodo/logs/pkgtest-%j.out
#
# END-TO-END TEST OF THE ZENODO PACKAGE.
#
# Runs the PACKAGED scripts (not the lab working copies) against the GEO clean
# room (only the 28 deposited files), writing to a scratch output directory.
# This is what a reader who downloads GSE348009 and the Zenodo archive gets.
set -uo pipefail
PKG=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Zenodo/ady3001-scseq-code-v1.0.0
REB=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild

module load R/4.4.0-gfbf-2023b
export ADY3001_DATA="$REB/geo/clean_room/unpacked"
export ADY3001_OUT="$REB/zenodo/pkgtest_output_v2"
export ADY3001_LIB="$REB/common/Rlib_pin:$REB/common/Rlib:/home/ayeh/R/x86_64-pc-linux-gnu-library/4.4"
export TMPDIR="${TMPDIR:-/loc/scratch/$SLURM_JOB_ID}"
mkdir -p "$ADY3001_OUT" "$TMPDIR"

echo "=== $(date) package end-to-end test ==="
echo "node : $(hostname)"
echo "pkg  : $PKG"
echo "data : $ADY3001_DATA"
echo "out  : $ADY3001_OUT"
echo
cd "$PKG"
bash ./run_all.sh
rc=$?
echo "=== $(date) run_all.sh exit $rc ==="
exit $rc
