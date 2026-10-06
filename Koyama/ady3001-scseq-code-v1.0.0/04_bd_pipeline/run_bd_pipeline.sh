#!/bin/bash
#SBATCH --partition=campus-new
#SBATCH --job-name=bd_rhap
#SBATCH --cpus-per-task=36
#SBATCH --mem=650G
#SBATCH --time=4-00:00:00
#SBATCH --output=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild/%x/logs/bd_%x_%j.out
#
# Re-run the BD Rhapsody WTA pipeline on the raw FASTQ, at the exact version
# the original Seven Bridges run used.
#
#   sbatch --job-name=Exp160 run_bd_pipeline.sh cartridge1
#   sbatch --job-name=Exp649 run_bd_pipeline.sh Cart1
#
# The pipeline version is chosen from the experiment, not passed in, so a run
# cannot silently be done with the wrong one:
#   Exp160 -> 1.9.1   (Metrics_Summary: "BD WTA Rhapsody Analysis Pipeline Version 1.9.1")
#   Exp649 -> 1.10.1  (Metrics_Summary: "BD Rhapsody WTA Analysis Pipeline Version 1.10.1")
set -euo pipefail

EXP="${SLURM_JOB_NAME:-${EXP:-}}"
EXP="${EXP%%-smoke}"
SAMPLE="${1:?usage: run_bd_pipeline.sh <sample> [smoke-fraction]   (sbatch --job-name=Exp160|Exp649)}"
SMOKE="${2:-}"      # e.g. 0.002 - subsample the reads to prove the plumbing works

REB=/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024/Rebuild
case "$EXP" in
  Exp160) VER=1.9.1  ;;
  Exp649) VER=1.10.1 ;;
  *) echo "job-name must be Exp160 or Exp649, got '$EXP'" >&2; exit 2 ;;
esac

# Use the null-safe copy (see patch_cwl_nullsafe_ram.py): identical to BD's file
# except that one VDJ RAM hint returns its own 2000 MB floor instead of NaN when
# no VDJ library is present, which cwltool 3.2 otherwise refuses at the very end
# of an otherwise-complete run. For v1.9.1 the copy is byte-identical to BD's.
CWL="$REB/common/scripts/cwl/v$VER/rhapsody_wta_$VER.nullsafe.cwl"
[[ -s $CWL ]] || CWL="$REB/common/scripts/cwl/v$VER/rhapsody_wta_$VER.cwl"
YML="$REB/$EXP/01_bd_pipeline/yml/$SAMPLE.yml"
OUT="$REB/$EXP/01_bd_pipeline/$SAMPLE"

# Scratch goes on the compute node's LOCAL disk, not the project allocation.
# Two reasons, both measured on the first run:
#   * singularity on this filesystem cannot loop-mount the .sif, so it unpacks the
#     whole 1.2 GB image into a ~6 GB sandbox under $APPTAINER_TMPDIR - for EVERY
#     one of the pipeline's 25 steps. On GPFS that is slow and fills the allocation;
#     on /loc/scratch it is local SSD and disappears with the job.
#   * the pipeline's own intermediates (split FASTQ, alignments) are large and
#     entirely disposable.
# /loc/scratch/$SLURM_JOB_ID is created for us and sits on a 7 TB local disk.
if [[ -n ${SLURM_JOB_ID:-} && -d /loc/scratch/${SLURM_JOB_ID} ]]; then
  TMP="/loc/scratch/${SLURM_JOB_ID}/bd_$SAMPLE"
else
  TMP="$REB/$EXP/01_bd_pipeline/.tmp_$SAMPLE"
  echo "WARNING: no /loc/scratch; falling back to project storage for scratch" >&2
fi

if [[ -n $SMOKE ]]; then
  # A subsampled run. It is NOT a reproduction of anything - it exists only to
  # prove that cwltool, singularity, the pinned image, the reference and the
  # rebuilt AbSeq FASTA all work together, in ~1 h instead of ~1 day.
  SMOKE_YML="$REB/$EXP/01_bd_pipeline/yml/${SAMPLE}.smoke.yml"
  { sed 's/^Run_Name:.*/#&/' "$YML"
    echo ""
    echo "Subsample: $SMOKE"
    echo "Subsample_seed: 3445"
  } > "$SMOKE_YML"
  YML="$SMOKE_YML"
  OUT="$REB/$EXP/01_bd_pipeline/${SAMPLE}_smoke"
  TMP="${TMP}_smoke"
  echo "SMOKE TEST: subsampling to $SMOKE of reads; output is not a reproduction"
fi

for f in "$CWL" "$YML"; do [[ -s $f ]] || { echo "missing $f" >&2; exit 3; }; done
mkdir -p "$OUT" "$TMP" "$REB/$EXP/logs"

module load Apptainer/1.1.6 2>/dev/null || module load Singularity/3.5.3 2>/dev/null || true
export MAMBA_ROOT_PREFIX=/home/ayeh/micromamba
eval "$(/home/ayeh/.local/bin/micromamba shell hook -s bash)"
micromamba activate bd_rhapsody

# Point every container/cache path inside the project so nothing lands in $HOME
export CWL_SINGULARITY_CACHE="$REB/common/containers"
# Keep the apptainer cache OUT of CWL_SINGULARITY_CACHE: cwltool os.walk()s that
# directory looking for the image, and the layer cache is thousands of files.
export APPTAINER_CACHEDIR="$TMP/.apptainer-cache"
export SINGULARITY_CACHEDIR="$APPTAINER_CACHEDIR"
export APPTAINER_TMPDIR="$TMP" SINGULARITY_TMPDIR="$TMP"
mkdir -p "$CWL_SINGULARITY_CACHE" "$APPTAINER_CACHEDIR" "$TMP"

echo "=== $(date) ==="
echo "experiment : $EXP"
echo "sample     : $SAMPLE"
echo "pipeline   : bdgenomics/rhapsody:$VER"
echo "cwl        : $CWL"
echo "yml        : $YML"
echo "outdir     : $OUT"
echo "node       : $(hostname)  cpus=${SLURM_CPUS_PER_TASK:-?}  mem=${SLURM_MEM_PER_NODE:-?}M"
cwltool --version

# Singularity on this cluster cannot loop-mount a .sif, so every container start
# UNPACKS the 1.2 GB image into a ~6 GB sandbox - 25+ times per workflow. Build the
# sandbox ONCE on local disk instead and hand it to cwltool with
# --singularity-sandbox-path, which looks for <base>/<dockerPull>, i.e.
# <base>/bdgenomics/rhapsody:<ver>. After this no step extracts anything.
SANDBOX_BASE="$TMP/sandbox"
SANDBOX="$SANDBOX_BASE/bdgenomics/rhapsody:$VER"
if [[ ! -d "$SANDBOX" ]]; then
  mkdir -p "$(dirname "$SANDBOX")"
  echo "building singularity sandbox once: $SANDBOX"
  t0=$SECONDS
  singularity build --sandbox "$SANDBOX" "$REB/common/containers/rhapsody-$VER.sif"
  echo "sandbox built in $((SECONDS-t0)) s"
fi

# cwltool derives the .sif filename from the dockerPull string. Ask cwltool
# itself rather than guessing, and link the pre-pulled image to that name so the
# run does not have to reach Docker Hub.
PRE="$REB/common/containers/rhapsody-$VER.sif"
if [[ -s $PRE ]]; then
  mapfile -t WANT < <(python3 - "$VER" <<'PY'
import sys
from cwltool.singularity import _normalize_image_id, _normalize_sif_id
tag = "bdgenomics/rhapsody:%s" % sys.argv[1]
print(_normalize_sif_id(tag))
print(_normalize_image_id(tag))
PY
)
  for w in "${WANT[@]}"; do
    [[ -n "$w" && ! -e "$CWL_SINGULARITY_CACHE/$w" ]] || continue
    ln -sf "$PRE" "$CWL_SINGULARITY_CACHE/$w"
    echo "linked pre-pulled image as $w"
  done
fi

cd "$OUT"
set -x
# Within one cartridge the workflow fans out: SplitAndSubsample cuts each FASTQ
# into 12,000,000-read chunks (~27 per lane, so ~54 read-pair chunks for a full
# cartridge), and AnnotateR1, AnnotateR2, AnnotateMolecules, AddtoBam and
# Dense_to_Sparse_Datatable all scatter over those chunks. cwltool runs a scatter
# SERIALLY unless told otherwise, which is where nearly all the wall-clock goes.
#
# --parallel-max is NOT a job count. In cwltool's MultithreadedJobExecutor it sets
# the executor's CORE BUDGET (executors.py: self.max_cores = max_parallel), and the
# executor refuses outright to start any step whose coresMin exceeds that budget:
#
#     Cannot make job: Requested at least 16 cores but only 12.0 available
#
# which is a permanentFail, not a wait. v1.9.1's AlignR2 asks for 16 cores and
# v1.10.1's for 8, so a budget of 12 silently works for Exp649 and kills Exp160 --
# three hours in, right after quality filtering. It must be >= the largest coresMin
# in the workflow, and there is no reason for it to be less than the CPUs we hold.
#
# Memory needs no separate guard: the same executor reads the node's available RAM
# and checks allocated_ram + ramMin against it before dispatching each job, so it
# throttles the 32 GB AnnotateMolecules scatter on its own.
PARALLEL_MAX="${PARALLEL_MAX:-${SLURM_CPUS_PER_TASK:-8}}"
MAX_CORES_MIN=$(python3 - "$CWL" <<'PY'
import json, sys
d = json.loads("\n".join(open(sys.argv[1]).read().split("\n")[1:]))
mx = 0
def scan(reqs):
    global mx
    for r in reqs or []:
        if isinstance(r, dict) and r.get("class") == "ResourceRequirement":
            c = r.get("coresMin")
            if isinstance(c, (int, float)):
                mx = max(mx, c)
for x in d["$graph"]:
    scan(x.get("requirements")); scan(x.get("hints"))
    for st in x.get("steps") or []:
        scan(st.get("requirements")); scan(st.get("hints"))
print(int(mx))
PY
)
echo "parallel-max: $PARALLEL_MAX core budget; largest coresMin in this workflow: $MAX_CORES_MIN"
if (( PARALLEL_MAX < MAX_CORES_MIN )); then
  echo "FATAL: --parallel-max $PARALLEL_MAX is below the workflow's largest coresMin" \
       "($MAX_CORES_MIN); cwltool would permanentFail on that step hours in." >&2
  exit 5
fi

cwltool \
  ${CWL_EXTRA:-} \
  --parallel --parallel-max "$PARALLEL_MAX" \
  --singularity \
  --singularity-sandbox-path "$SANDBOX_BASE" \
  --outdir "$OUT" \
  --tmpdir-prefix "$TMP/" \
  --tmp-outdir-prefix "$TMP/" \
  --leave-tmpdir \
  --timestamps \
  --relax-path-checks \
  "$CWL" "$YML"
rc=$?
set +x

echo "=== cwltool exit $rc  $(date) ==="
# Local scratch vanishes with the job, so on failure pull the step logs out first -
# they are the only diagnostic left once the node is released.
if [[ $rc -ne 0 ]]; then
  SAVE="$REB/$EXP/logs/failed_${SAMPLE}_${SLURM_JOB_ID:-manual}"
  mkdir -p "$SAVE"
  find "$TMP" -maxdepth 3 -name "*.log" -o -maxdepth 3 -name "output.txt" 2>/dev/null \
    | head -200 | while read -r f; do cp --parents "$f" "$SAVE" 2>/dev/null || true; done
  echo "saved step logs to $SAVE"
else
  rm -rf "$TMP"
  ls -l "$OUT"
fi
exit $rc
