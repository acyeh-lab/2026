#!/usr/bin/env python3
"""
Make one RAM-hint expression in BD's v1.10.1 WTA CWL null-safe.

Why this is needed
------------------
Exp649's run declared `VDJ Version: None`, so the VDJ branch of the workflow has
nothing to do. BD's CWL still carries the VDJ steps, and the step
`VDJ_Preprocess_Reads.cwl/VDJ_RSEC_Reads` sets its memory hint from a JavaScript
expression over `inputs.num_valid_reads`. With no VDJ library that input is null,
`parseInt(null)` is NaN, and cwltool 3.2 refuses to build the job:

    Cannot make job: rhapsody_wta_1.10.1.cwl:5012:29:
    union[int, float] object expected; got None

BD ran these workflows on Seven Bridges, whose runner tolerated it. cwltool does
not. The whole WTA branch completes first - AnnotateReads and everything before it
succeed - and then the run is marked permanentFail at the very end, so no outputs
are copied out.

What this changes
-----------------
Exactly one thing: the expression returns the 2000 MB floor it already defines
when `num_valid_reads` is absent, instead of NaN. It is a *resource hint* on a
step that does not execute in these runs. No analysis parameter, no tool
argument, no reference, no threshold is touched.

v1.9.1 (Exp160) contains no JavaScript resource expressions at all and needs no
patch; this script is a no-op for it.

The original file is left untouched; the patched copy is written alongside with a
.nullsafe.cwl suffix and a .patch.txt recording the before/after.
"""
import os, re, sys, difflib

HERE = os.path.dirname(os.path.abspath(__file__))
TARGETS = [
    os.path.join(HERE, "cwl/v1.9.1/rhapsody_wta_1.9.1.cwl"),
    os.path.join(HERE, "cwl/v1.10.1/rhapsody_wta_1.10.1.cwl"),
]

OLD = ("${ var est_ram = 0.0006 * parseInt(inputs.num_valid_reads) + 2000; "
       "var buffer = 1.25; est_ram *= buffer; if (est_ram < 2000) return 2000; "
       "if (est_ram > 370000) return 370000; return parseInt(est_ram); }")
NEW = ("${ if (inputs.num_valid_reads === null || inputs.num_valid_reads === undefined) "
       "return 2000; var est_ram = 0.0006 * parseInt(inputs.num_valid_reads) + 2000; "
       "var buffer = 1.25; est_ram *= buffer; if (isNaN(est_ram)) return 2000; "
       "if (est_ram < 2000) return 2000; if (est_ram > 370000) return 370000; "
       "return parseInt(est_ram); }")


def patch(path):
    src = open(path).read()
    out = path.replace(".cwl", ".nullsafe.cwl")
    n = src.count(OLD)
    if n == 0:
        # still emit the copy so the runner can use one filename everywhere
        open(out, "w").write(src)
        print(f"{os.path.basename(path)}: no null-unsafe RAM expression (copy written)")
        return out, 0
    dst = src.replace(OLD, NEW)
    open(out, "w").write(dst)
    with open(out.replace(".cwl", ".patch.txt"), "w") as fh:
        fh.write(f"# {os.path.basename(path)} -> {os.path.basename(out)}\n")
        fh.write(f"# {n} occurrence(s) of the VDJ_RSEC_Reads ramMin expression\n\n")
        fh.write("- " + OLD + "\n\n+ " + NEW + "\n")
    print(f"{os.path.basename(path)}: patched {n} occurrence(s) -> {os.path.basename(out)}")
    return out, n


if __name__ == "__main__":
    for t in TARGETS:
        if not os.path.exists(t):
            print(f"missing: {t}", file=sys.stderr); sys.exit(1)
        patch(t)
