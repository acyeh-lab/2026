#!/usr/bin/env python3
"""
Compare a rebuilt BD RSEC matrix against the original Seven Bridges one.

This is the test that decides whether Part 1 worked. It reports, per cartridge:

  * metrics agreement  - Total_Reads_in_FASTQ, putative cell count, total molecules
  * feature agreement  - identical set of gene / pAbO column names?
  * cell agreement     - identical set of Cell_Index values?
  * count agreement    - on the shared cells and shared features, exact equality,
                         and if not exact, the Pearson r of the per-cell totals

It deliberately does NOT declare a tolerance. If the counts are not exactly equal
that is a finding to look at, not something to wave through; the numbers are printed
so the size of the difference is visible.

    python3 compare_matrices.py Exp160 cartridge1
    python3 compare_matrices.py --all
"""
import argparse, os, re, sys, csv, math

ROOT = "/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024"
REB  = os.path.join(ROOT, "Rebuild")

MAP = {
    "Exp160": {"cartridge1": "cart1", "cartridge2": "cart2", "cartridge3": "cart3"},
    "Exp649": {"Cart1": "cart1", "Cart2": "cart2"},
}

def orig_path(exp, cart, kind="RSEC"):
    return os.path.join(ROOT, exp, "data", MAP[exp][cart],
                        f"{cart}_{kind}_MolsPerCell.csv")

def reb_path(exp, cart, kind="RSEC"):
    d = os.path.join(REB, exp, "01_bd_pipeline", cart)
    if not os.path.isdir(d): return None
    for f in os.listdir(d):
        if f.endswith(f"_{kind}_MolsPerCell.csv"):
            return os.path.join(d, f)
    return None

def metrics_path(p):
    d, b = os.path.dirname(p), os.path.basename(p)
    s = b.split("_")[0]
    for f in os.listdir(d):
        if f.endswith("_Metrics_Summary.csv"):
            return os.path.join(d, f)
    return None

def parse_metrics(p):
    """Pull a few headline numbers out of a BD Metrics_Summary.csv."""
    if not p or not os.path.exists(p): return {}
    txt = open(p, errors="replace").read()
    out = {}
    m = re.search(r"Total_Reads_in_FASTQ[^\n]*\n([0-9]+)", txt)
    if m: out["Total_Reads_in_FASTQ"] = int(m.group(1))
    # first Putative_Cell_Count under "#Cells RSEC#"
    m = re.search(r"#Cells RSEC#\n[^\n]*\n([0-9]+)", txt)
    if m: out["Putative_Cell_Count"] = int(m.group(1))
    m = re.search(r"\n([0-9]+),[0-9]+,[0-9]+,[0-9]+,[^\n]*,mRNA\n", txt)
    if m: out["Aligned_Reads_mRNA"] = int(m.group(1))
    return out

def header_and_index(path):
    """Return (feature names, {cell_index: row_offset}) without loading counts."""
    feats, cells = None, []
    with open(path, newline="", errors="replace") as fh:
        for line in fh:
            if line.startswith("#"): continue
            feats = line.rstrip("\n").split(",")[1:]
            break
        for line in fh:
            if not line.strip(): continue
            cells.append(line.split(",", 1)[0])
    return feats, cells

def totals_per_cell(path, want_feats=None):
    """Sum of counts per cell, restricted to want_feats if given."""
    with open(path, newline="", errors="replace") as fh:
        for line in fh:
            if line.startswith("#"): continue
            feats = line.rstrip("\n").split(",")[1:]
            break
        keep = None
        if want_feats is not None:
            idx = {f: i for i, f in enumerate(feats)}
            keep = [idx[f] for f in want_feats if f in idx]
        out = {}
        for line in fh:
            if not line.strip(): continue
            parts = line.rstrip("\n").split(",")
            cid = parts[0]
            vals = parts[1:]
            if keep is None:
                out[cid] = sum(int(v) for v in vals if v)
            else:
                out[cid] = sum(int(vals[i]) for i in keep if vals[i])
    return out

def pearson(a, b):
    n = len(a)
    if n < 2: return float("nan")
    ma, mb = sum(a)/n, sum(b)/n
    va = sum((x-ma)**2 for x in a); vb = sum((x-mb)**2 for x in b)
    if va == 0 or vb == 0: return float("nan")
    cov = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    return cov / math.sqrt(va*vb)

def compare(exp, cart, kind="RSEC"):
    o = orig_path(exp, cart, kind)
    r = reb_path(exp, cart, kind)
    print(f"\n=== {exp} / {cart} / {kind} ===")
    if not os.path.exists(o):
        print(f"  original missing: {o}"); return
    if not r:
        print("  rebuilt matrix not present - BD pipeline has not been run for this cartridge")
        return
    print(f"  original: {o}")
    print(f"  rebuilt : {r}")

    mo, mr = parse_metrics(metrics_path(o)), parse_metrics(metrics_path(r))
    for k in sorted(set(mo) | set(mr)):
        a, b = mo.get(k), mr.get(k)
        flag = "MATCH" if a == b else "DIFFERS"
        print(f"  {k:26s} original={a!s:>14} rebuilt={b!s:>14}  {flag}")

    fo, co = header_and_index(o)
    fr, cr = header_and_index(r)
    sfo, sfr, sco, scr = set(fo), set(fr), set(co), set(cr)
    print(f"  features : original {len(fo):,}  rebuilt {len(fr):,}  shared {len(sfo & sfr):,}"
          f"  only-original {len(sfo - sfr):,}  only-rebuilt {len(sfr - sfo):,}")
    print(f"  cells    : original {len(co):,}  rebuilt {len(cr):,}  shared {len(sco & scr):,}"
          f"  only-original {len(sco - scr):,}  only-rebuilt {len(scr - sco):,}")
    if sfo != sfr:
        ex = list(sfo - sfr)[:5] + list(sfr - sfo)[:5]
        print(f"    example differing features: {ex}")

    shared_f = sorted(sfo & sfr)
    to = totals_per_cell(o, shared_f)
    tr = totals_per_cell(r, shared_f)
    shared_c = sorted(sco & scr)
    if not shared_c:
        print("  no shared cells - cannot compare counts"); return
    a = [to[c] for c in shared_c]; b = [tr[c] for c in shared_c]
    exact = sum(1 for x, y in zip(a, b) if x == y)
    print(f"  per-cell molecule totals over {len(shared_c):,} shared cells, "
          f"{len(shared_f):,} shared features:")
    print(f"    identical for {exact:,} / {len(shared_c):,} cells "
          f"({100.0*exact/len(shared_c):.2f} %)")
    print(f"    Pearson r = {pearson(a, b):.6f}")
    if exact != len(shared_c):
        d = [abs(x-y) for x, y in zip(a, b) if x != y]
        print(f"    of the differing cells: median |diff| = {sorted(d)[len(d)//2]}, "
              f"max = {max(d)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment", nargs="?")
    ap.add_argument("cartridge", nargs="?")
    ap.add_argument("--kind", default="RSEC", choices=["RSEC", "DBEC"])
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if a.all or not a.experiment:
        for exp, carts in MAP.items():
            for cart in carts:
                compare(exp, cart, a.kind)
    else:
        compare(a.experiment, a.cartridge, a.kind)
