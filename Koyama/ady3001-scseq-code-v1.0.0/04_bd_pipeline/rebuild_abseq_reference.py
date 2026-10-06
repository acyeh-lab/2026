#!/usr/bin/env python3
"""
Reconstruct the two AbSeq reference FASTAs that the Seven Bridges runs consumed
but that were never written to disk here:

    Exp160  AbSeq_Ref_Motoko_Melissa_12042020.fasta      (4 pAbO)
    Exp649  Exp649_Abseq_and_CD326_ref_07132022.fasta    (7 pAbO)

Method, and why it is exact rather than a guess:

  * The pAbO panel of each run is recorded in that run's own output. The
    header line of <sample>_RSEC_MolsPerCell.csv names every AbSeq target in
    BD's 4-field form, e.g.

        CD326:G8.8-AMM2281|Epcam|AMM2281|pAbO

    That string is the FASTA record name the pipeline used, character for
    character - the pipeline writes the reference's own header as the column.

  * The nucleotide barcode for each of those SeqIDs is published by BD in the
    cumulative AbSeq reference at
        s3://bd-rhapsody-public/AbSeq-references/BDAbSeq_allReference_<date>.fasta
    We take each experiment's barcodes from the last BD release that PREDATES
    that experiment's own reference date, so no later re-issue of a barcode can
    leak in:
        Exp160 (ref dated 2020-12-04) -> BDAbSeq_allReference_2020_08_20.fasta
        Exp649 (ref dated 2022-07-13) -> BDAbSeq_allReference_2022_03_17.fasta

  * Independent check: the four Exp160 barcodes are also printed on the BD
    technical data sheets kept in Exp160/ (940118 CD45.2, 940123 I-A/I-E,
    940164 H-2Kb, 940169 CD326). The script verifies the S3 sequence against
    the data sheet where a sheet exists.

Writes, for each experiment, the FASTA plus a .provenance.txt recording where
every base came from.
"""
import argparse, os, re, sys

ROOT = "/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024"
REBUILD = os.path.join(ROOT, "Rebuild")
ABSEQ_DIR = os.path.join(REBUILD, "common", "abseq")

EXPERIMENTS = {
    "Exp160": dict(
        csv=os.path.join(ROOT, "Exp160/data/cart1/cartridge1_RSEC_MolsPerCell.csv"),
        master=os.path.join(ABSEQ_DIR, "BDAbSeq_allReference_2020_08_20.fasta"),
        out=os.path.join(ABSEQ_DIR, "AbSeq_Ref_Motoko_Melissa_12042020.rebuilt.fasta"),
        original_name="AbSeq_Ref_Motoko_Melissa_12042020.fasta",
        # barcode sequences transcribed from the BD technical data sheets in Exp160/
        datasheets={
            "AMM2014": ("940118--CD45.2.pdf", "TGGTAACGTAGCTCGGGAATAAGTAATGCGGAAGTC"),
            "AMM2019": ("940123--IAIE.pdf",   "TTTATGCGAGAGGTTAGGTAGGCCCGAGTTTAGTGG"),
            "AMM2060": ("940164--H2Kb.pdf",   "CGGTATATATCTCGGAGGTAAGCGTCGCGGAAATGT"),
            "AMM2065": ("940169--CD326.pdf",  "AGAGTTGAGTGGGTTGGTCGAGTAGCGTAAATGTGG"),
        },
    ),
    "Exp649": dict(
        csv=os.path.join(ROOT, "Exp649/data/cart1/Cart1_RSEC_MolsPerCell.csv"),
        master=os.path.join(ABSEQ_DIR, "BDAbSeq_allReference_2022_03_17.fasta"),
        out=os.path.join(ABSEQ_DIR, "Exp649_Abseq_and_CD326_ref_07132022.rebuilt.fasta"),
        original_name="Exp649_Abseq_and_CD326_ref_07132022.fasta",
        datasheets={
            "AMM2014": ("940118--CD45.2.pdf", "TGGTAACGTAGCTCGGGAATAAGTAATGCGGAAGTC"),
            "AMM2019": ("940123--IAIE.pdf",   "TTTATGCGAGAGGTTAGGTAGGCCCGAGTTTAGTGG"),
            "AMM2060": ("940164--H2Kb.pdf",   "CGGTATATATCTCGGAGGTAAGCGTCGCGGAAATGT"),
            "AMM2065": ("940169--CD326.pdf",  "AGAGTTGAGTGGGTTGGTCGAGTAGCGTAAATGTGG"),
        },
    ),
}


def panel_from_csv(path):
    """Return the ordered list of pAbO column names in a BD MolsPerCell csv."""
    cols = None
    with open(path) as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            cols = line.rstrip("\n").split(",")
            break
    if cols is None:
        raise RuntimeError(f"no header line in {path}")
    if cols[0] != "Cell_Index":
        raise RuntimeError(f"{path}: first column is {cols[0]!r}, expected Cell_Index")
    pabo = [c for c in cols if c.endswith("|pAbO")]
    if not pabo:
        raise RuntimeError(f"{path}: no |pAbO columns found")
    return pabo


def read_fasta(path):
    """name (first whitespace-delimited token of the header) -> (full_header, seq)."""
    out, name, hdr, buf = {}, None, None, []
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if name is not None:
                    out[name] = (hdr, "".join(buf))
                hdr = line[1:]
                name = hdr.split()[0]
                buf = []
            elif line:
                buf.append(line.strip())
    if name is not None:
        out[name] = (hdr, "".join(buf))
    return out


def build(exp, cfg, verbose=True):
    panel = panel_from_csv(cfg["csv"])
    master = read_fasta(cfg["master"])

    records, prov = [], []
    prov.append(f"# Reconstructed AbSeq reference for {exp}")
    prov.append(f"# original (not on disk): {cfg['original_name']}")
    prov.append(f"# panel taken from : {cfg['csv']}")
    prov.append(f"# barcodes taken from: {os.path.basename(cfg['master'])}")
    prov.append(f"# targets: {len(panel)}")
    prov.append("")

    missing = []
    for col in panel:
        if col not in master:
            missing.append(col)
            continue
        hdr, seq = master[col]
        records.append((col, seq))
        seqid = col.split("|")[2]
        note = ""
        ds = cfg["datasheets"].get(seqid)
        if ds:
            sheet, ds_seq = ds
            note = ("  datasheet %s: MATCH" % sheet) if ds_seq == seq \
                   else ("  datasheet %s: MISMATCH (%s)" % (sheet, ds_seq))
        prov.append(f"{col}\t{seq}\tfrom_header={hdr}{note}")
        if ds and ds[1] != seq:
            raise RuntimeError(f"{exp} {seqid}: S3 barcode disagrees with data sheet {ds[0]}")

    if missing:
        raise RuntimeError(f"{exp}: not found in master reference: {missing}")

    with open(cfg["out"], "w") as fh:
        for name, seq in records:
            fh.write(f">{name}\n{seq}\n")
    with open(cfg["out"] + ".provenance.txt", "w") as fh:
        fh.write("\n".join(prov) + "\n")

    if verbose:
        print(f"{exp}: wrote {len(records)} records -> {cfg['out']}")
        for name, seq in records:
            print(f"    {name}  {seq}  ({len(seq)} nt)")
    return cfg["out"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("experiments", nargs="*", default=None)
    a = ap.parse_args()
    todo = a.experiments or list(EXPERIMENTS)
    for e in todo:
        build(e, EXPERIMENTS[e])
