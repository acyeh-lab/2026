#!/bin/bash
# Check that builders/ still matches its authoritative copies elsewhere in the
# project. The two can drift if someone edits one and not the other.
#   ./sync_builders.sh          report only
#   ./sync_builders.sh --pull   copy the authoritative versions into builders/
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJ=$(dirname "$HERE")
PULL=0; [ "${1:-}" = "--pull" ] && PULL=1
declare -A SRC=(
  [build_zenodo_package.py]="$PROJ/Rebuild/zenodo/build_zenodo_package.py"
  [package_docs.py]="$PROJ/Rebuild/zenodo/package_docs.py"
  [run_package_test.sh]="$PROJ/Rebuild/zenodo/run_package_test.sh"
  [build_zenodo_report.py]="$PROJ/Sci_Imm_Revision/build_zenodo_report.py"
)
drift=0
for f in "${!SRC[@]}"; do
  s="${SRC[$f]}"; d="$HERE/builders/$f"
  if [ ! -f "$s" ]; then echo "  SOURCE MISSING  $s"; drift=$((drift+1)); continue; fi
  if cmp -s "$s" "$d"; then
    echo "  same     $f"
  else
    echo "  DRIFTED  $f"; drift=$((drift+1))
    [ "$PULL" = 1 ] && { cp "$s" "$d" && echo "           pulled from $s"; }
  fi
done
echo
if [ "$drift" -eq 0 ]; then echo "### IN SYNC"; else
  echo "### $drift file(s) differ"
  [ "$PULL" = 0 ] && echo "Run ./sync_builders.sh --pull to update builders/."
fi
