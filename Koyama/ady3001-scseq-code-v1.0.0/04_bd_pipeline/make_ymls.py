#!/usr/bin/env python3
"""
Write one BD CWL input YML per cartridge, from the verified raw FASTQ locations.

Inputs are pinned to what each original run actually declared in its own
Metrics_Summary header:

  Exp160  pipeline 1.9.1   AbSeq ref AbSeq_Ref_Motoko_Melissa_12042020.fasta
                           + "Supplemental sequences: combined_extra_seq.fasta"
  Exp649  pipeline 1.10.1  references gencodevM19-20181206.gtf
                           | GRCm38-PhiX-gencodevM19-20181206.tar.gz
                           | Exp649_Abseq_and_CD326_ref_07132022.fasta

Neither original AbSeq FASTA survives; both are rebuilt byte-exact by
rebuild_abseq_reference.py and used here. combined_extra_seq.fasta does NOT
survive and is NOT reconstructible - see the methods page. No supplemental
sequence appears as a column in the Exp160 output, so it contributed no
detected target, but the run is declared as "reference incomplete" for that
reason rather than claimed identical.
"""
import os, sys, glob

ROOT = "/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024"
REB = os.path.join(ROOT, "Rebuild")
REFS = os.path.join(REB, "common", "refs")
ABSEQ = os.path.join(REB, "common", "abseq")

GENOME = os.path.join(REFS, "GRCm38-PhiX-gencodevM19-20181206.tar.gz")
GTF    = os.path.join(REFS, "gencodevM19-20181206.gtf")

EXP160_FQ = "/shared/ngs/illumina/kensbey/201019_A00613_0188_BHTK53DRXX/Unaligned/Project_kensbey"
EXP649_FQ = "/fh/fast/hill_g/Rhapsody/fastq/220706_VH00738_51_AAAN5GVHV"

RUNS = {
    "Exp160": dict(
        version="1.9.1",
        abseq=os.path.join(ABSEQ, "AbSeq_Ref_Motoko_Melissa_12042020.rebuilt.fasta"),
        samples={
            "cartridge1": [f"{EXP160_FQ}/cartridge1_S1_R1_001.fastq.gz",
                           f"{EXP160_FQ}/cartridge1_S1_R2_001.fastq.gz"],
            "cartridge2": [f"{EXP160_FQ}/cartridge2_S2_R1_001.fastq.gz",
                           f"{EXP160_FQ}/cartridge2_S2_R2_001.fastq.gz"],
            "cartridge3": [f"{EXP160_FQ}/cartridge3_S3_R1_001.fastq.gz",
                           f"{EXP160_FQ}/cartridge3_S3_R2_001.fastq.gz"],
        },
    ),
    "Exp649": dict(
        version="1.10.1",
        abseq=os.path.join(ABSEQ, "Exp649_Abseq_and_CD326_ref_07132022.rebuilt.fasta"),
        samples={
            # both lanes go into one run - the pipeline concatenates them, which
            # is how the original Total_Reads_in_FASTQ (L001+L002) was produced
            "Cart1": [f"{EXP649_FQ}/Cart1_S1_L00{l}_R{r}_001.fastq.gz"
                      for l in (1, 2) for r in (1, 2)],
            "Cart2": [f"{EXP649_FQ}/Cart2_S2_L00{l}_R{r}_001.fastq.gz"
                      for l in (1, 2) for r in (1, 2)],
        },
    ),
}


def write_yml(exp, sample, reads, abseq, path):
    lines = [
        "#!/usr/bin/env cwl-runner",
        "",
        "cwl:tool: rhapsody",
        "",
        f"# {exp} / {sample} - rebuild of the original Seven Bridges run",
        f"# pipeline: bdgenomics/rhapsody:{RUNS[exp]['version']}",
        "",
        "Reads:",
    ]
    for r in reads:
        lines += ["", " - class: File", f'   location: "{r}"']
    lines += [
        "",
        "Reference_Genome:",
        "   class: File",
        f'   location: "{GENOME}"',
        "",
        "Transcriptome_Annotation:",
        "   class: File",
        f'   location: "{GTF}"',
        "",
        "AbSeq_Reference:",
        " - class: File",
        f'   location: "{abseq}"',
        "",
        f'Run_Name: "{sample}"' if RUNS[exp]["version"] != "1.9.1" else "",
        "",
        "# Putative cell calling: left at the pipeline default (refined algorithm on,",
        "# no exact cell count), which is what Exp649's own metrics header records",
        "# as 'Refined Putative Cell Calling: On | Exact Cell Count: None'.",
        "# No sample tags were used in either run (Sample Tag Version: None) - the",
        "# Exp649 groups were encoded with four CD326 AbSeq oligos, not BD sample tags.",
    ]
    with open(path, "w") as fh:
        fh.write("\n".join(l for l in lines if l is not None) + "\n")


def main():
    missing = []
    for exp, cfg in RUNS.items():
        outdir = os.path.join(REB, exp, "01_bd_pipeline", "yml")
        os.makedirs(outdir, exist_ok=True)
        for sample, reads in cfg["samples"].items():
            for r in reads:
                if not os.path.exists(r):
                    missing.append(r)
            p = os.path.join(outdir, f"{sample}.yml")
            write_yml(exp, sample, reads, cfg["abseq"], p)
            print(f"wrote {p}  ({len(reads)} FASTQ)")
        if not os.path.exists(cfg["abseq"]):
            missing.append(cfg["abseq"])
    for p in (GENOME, GTF):
        if not os.path.exists(p):
            missing.append(p + "   (fetch_bd_assets.sh still running?)")
    if missing:
        print("\nMISSING INPUTS:", file=sys.stderr)
        for m in missing:
            print("  " + m, file=sys.stderr)
        sys.exit(1)
    print("\nall declared inputs present")


if __name__ == "__main__":
    main()
