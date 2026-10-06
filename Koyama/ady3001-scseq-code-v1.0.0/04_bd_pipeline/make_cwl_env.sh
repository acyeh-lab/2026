#!/bin/bash
# Creates the micromamba env that drives the BD CWL workflows.
#   cwltool  - the reference CWL runner; BD's own docs use cwl-runner
#   nodejs   - cwltool needs a JS engine for the $(inputs...) expressions in the CWL
#   python   - 3.11 (the system python3 on rhino is 3.6)
set -euo pipefail
export MAMBA_ROOT_PREFIX=/home/ayeh/micromamba
eval "$(/home/ayeh/.local/bin/micromamba shell hook -s bash)"
micromamba create -y -n bd_rhapsody -c conda-forge \
    python=3.11 nodejs 'cwltool>=3.1' 
micromamba activate bd_rhapsody
cwltool --version
node --version
