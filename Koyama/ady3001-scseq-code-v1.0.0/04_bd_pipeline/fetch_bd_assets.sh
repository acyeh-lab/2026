#!/bin/bash
#SBATCH --partition=campus-new
#SBATCH --job-name=bd_fetch
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --output=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild/common/scripts/logs/bd_fetch-%j.out
set -euo pipefail

REBUILD=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild
REFS=$REBUILD/common/refs
CONT=$REBUILD/common/containers
S3=https://bd-rhapsody-public.s3.amazonaws.com
mkdir -p "$REFS" "$CONT"

echo "=== $(date) BD asset fetch ==="

# --- 1. WTA reference: the exact pair named in Exp649's metrics header, and the
#        v1.x mouse reference both runs used. 24.1 GB + 0.8 GB.
cd "$REFS"
for f in GRCm38-PhiX-gencodevM19-20181206.tar.gz gencodevM19-20181206.gtf ; do
  if [[ -s $f ]]; then echo "have $f"; continue; fi
  echo "-- downloading $f"
  curl -fSL --progress-bar --retry 5 --retry-delay 10 -C - -o "$f" \
    "$S3/Rhapsody-WTA/Pipeline-version1.x_WTA_references/GRCm38-PhiX-gencodevM19/$f"
  ls -l "$f"
done

# tar listing is the only integrity check BD publishes no checksum for
# `tar | head` would hand tar a SIGPIPE, which `set -o pipefail` turns into a
# job failure (exit 141) even though the download is fine. List once into a file.
echo "-- verifying tarball is readable"
tar -tzf GRCm38-PhiX-gencodevM19-20181206.tar.gz > ref_tarball.listing
echo "   entries: $(wc -l < ref_tarball.listing)"
head -5 ref_tarball.listing
# BD ships the STAR index as ONE top-level directory; the pipeline errors otherwise.
top=$(cut -d/ -f1 ref_tarball.listing | sort -u | wc -l)
echo "   top-level entries: $top (must be 1)"
[[ $top -eq 1 ]] || { echo "unexpected tarball layout" >&2; exit 4; }

# --- 2. Pipeline images, pinned to the exact tags the two CWL workflows name.
module load Apptainer/1.1.6 2>/dev/null || module load Singularity/3.5.3 2>/dev/null || true
export APPTAINER_CACHEDIR=$CONT/.cache SINGULARITY_CACHEDIR=$CONT/.cache  # removed at the end
mkdir -p "$APPTAINER_CACHEDIR"
cd "$CONT"
for tag in 1.9.1 1.10.1; do
  sif="rhapsody-${tag}.sif"
  if [[ -s $sif ]]; then echo "have $sif"; continue; fi
  echo "-- pulling bdgenomics/rhapsody:$tag"
  singularity pull "$sif" "docker://bdgenomics/rhapsody:$tag"
  ls -l "$sif"
done

# The docker-layer cache is ~5.8 GB and is only needed while pulling. Both SIFs
# are self-contained once built, and cwltool os.walk()s CWL_SINGULARITY_CACHE
# looking for the image, so leaving it there is both wasted space and wasted IO.
rm -rf "$APPTAINER_CACHEDIR"

echo "=== $(date) DONE ==="
ls -l "$REFS" "$CONT"
