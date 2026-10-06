#!/usr/bin/env python3
"""
Build a side-by-side contact sheet of rebuilt panels against the original PDFs
that went into the manuscript.

Figures are judged by eye, not by checksum: UMAP rotation, cluster renumbering
and permutation-based p-values all move between runs without anything being
wrong (see methods.html section 9). So this renders each pair at the same size
into one HTML page and leaves the judgement to a person.

    module load Python/3.11.5-GCCcore-13.2.0
    python3 compare_figures.py Exp160 --rebuilt out_original_RSEC
"""
import argparse, os, re, subprocess, sys, html as H, datetime

sys.path.insert(0, "/home/ayeh/.claude/skills/html_report")
from house_report import head, toc, layout_open, layout_close, TOC_JS, verify

ROOT = "/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024"
REB  = os.path.join(ROOT, "Rebuild")

# rebuilt basename (without the [Fig..] tag)  ->  original figs/ basename
PAIRS = {
 "Exp160": {
  "[Fig4B] Initial Clustering, res=0.15, dim=40": "[Final] - Initial Clustering, res=0.15, dim=40.pdf",
  "[Fig4B] Initial Clustering by cart":           "[Final] - Initial Clustering by cart.pdf",
  "[Fig4B] Markers dotplot":                      "[Final] - Markers.pdf",
  "[Fig4C] GOCC_MHC_CLASS_II_PROTEIN_COMPLEX":    "[Final] - GOCC_MHC_CLASS_II_PROTEIN_COMPLEX.pdf",
  "[Fig4C] GOCC_MHC_CLASS_II_PROTEIN_COMPLEX violin": "[Final] - GOCC_MHC_CLASS_II_PROTEIN_COMPLEX violin.pdf",
  "[Fig4C] GOCC_MHC_CLASS_I_PROTEIN_COMPLEX":     "[Final] - GOCC_MHC_CLASS_I_PROTEIN_COMPLEX.pdf",
  "[Fig4C] GOCC_MHC_CLASS_I_PROTEIN_COMPLEX violin": "[Final] - GOCC_MHC_CLASS_I_PROTEIN_COMPLEX violin.pdf",
  "[Fig4C] GOBP_ANTIGEN_PROCESSING_AND_PRESENTATION": "[Final] - GOBP_ANTIGEN_PROCESSING_AND_PRESENTATION.pdf",
  "[Fig4C] GOBP_ANTIGEN_PROCESSING_AND_PRESENTATION violin": "[Final] - GOBP_ANTIGEN_PROCESSING_AND_PRESENTATION violin.pdf",
  "[Fig4D] I-A-I-E":                              "[Final] - I-A-I-E.pdf",
  "[Fig4D] I-A-I-E (violin)":                     "[Final] - I-A-I-E (violin).pdf",
  "[Fig4D] H-2Kb":                                "[Final] - H-2Kb.pdf",
  "[Fig4D] H-2Kb (violin)":                       "[Final] - H-2Kb (violin).pdf",
  "[FigS6A] Custom Stem_Cell":                    "[Final] - Custom Stem_Cell.pdf",
  "[FigS6A] Custom Goblet":                       "[Final] - Custom Goblet.pdf",
  "[FigS6A] Custom Tuft":                         "[Final] - Custom Tuft.pdf",
  "[FigS6A] Custom Paneth":                       "[Final] - Custom Paneth.pdf",
  "[FigS6A] Custom Enterocytes":                  "[Final] - Custom Enterocytes.pdf",
  "[FigS6A] Custom Enteroendocrine":              "[Final] - Custom Enteroendocrine.pdf",
  "[FigS6A] Custom Partial_IEC":                  "[Final] - Custom Partial_IEC.pdf",
  "[FigS6A] Custom Malagola_2024":                "[Revision] - Custom Malagola_2024.pdf",
  "[FigS6B] Pseudotime":                          "[Final] - Pseudotime.pdf",
  "[FigS6C] Lgr5":                                "[Revision] - Lgr5.pdf",
  "[FigS6C] Lgr4":                                "[Revision] - Lgr4.pdf",
  "[FigS6C] Fgfbp1":                              "[Revision] - Fgfbp1.pdf",
  "[FigS6D] Markers GSEA dotplot":                "[Final] - Markers GSEA.pdf",
  "[FigS6E] Markers ADT dotplot":                 "[Final] - Markers ADT.pdf",
  "[FigS7B] Cart2 v Cart3 by cart":               "[Revision] - Cart3 Overlay - Re-embed wih Cart2.pdf",
  "[FigS7B] Cart2 v Cart3 clusters, res=0.1, dim=40": "[Revision] - Cart3 Overlay - Re-embed wih Cart2; res=0.1, dim=40.pdf",
  "[FigS7B] Propeller_plots":                     "[Revision] - Propeller_plots.pdf",
  "[FigS7D] GOCC_MHC_CLASS_II_PROTEIN_COMPLEX":   "[Revision] - Cart3 Overlay - GOCC_MHC_CLASS_II_PROTEIN_COMPLEX.pdf",
  "[FigS7D] GOCC_MHC_CLASS_I_PROTEIN_COMPLEX":    "[Revision] - Cart3 Overlay - GOCC_MHC_CLASS_I_PROTEIN_COMPLEX.pdf",
  "[FigS7D] GOBP_ANTIGEN_PROCESSING_AND_PRESENTATION": "[Revision] - Cart3 Overlay - GOBP_ANTIGEN_PROCESSING_AND_PRESENTATION.pdf",
  "[FigS7E] DEG cluster 0v2 top 30":              "[Revision] - DEG Cart 2v3 cluster 0v2 top 30.pdf",
  "[FigS7E] DEG cluster 0v2 top 150":             "[Revision] - DEG Cart 2v3 cluster 0v2 top 150.pdf",
  "[FigS7E] top DEGs featureplots":               "[Revision] - top DEGs.pdf",
 },
 "Exp649": {
  "[FigS10A] QC Clusters":       "[Final] - QC Clusters.pdf",
  "[FigS10B-D] QC Lgr5":         "[Final] - QC Lgr5.pdf",
  "[FigS10B] QC Lgr5 Exp Level": "[Final] - QC Lgr5 Exp Level.pdf",
  "[FigS10B-D] QC Muc2":         "[Final] - QC Muc2.pdf",
  "[FigS10B-D] QC Trpm5":        "[Final] - QC Trpm5.pdf",
  "[Fig7D] Clusters":            "[Final] - Clusters.pdf",
  "[Fig7B] Groups":              "[Final] - Groups.pdf",
  "[Fig7E] Ciita":               "[Final] - Ciita.pdf",
  "[Fig7E] H2-Aa":               "[Final] - H2-Aa.pdf",
  "[Fig7E] H2-Ab1":              "[Final] - H2-Ab1.pdf",
  "[Fig7E] Mki67":               "[Final] - Mki67.pdf",
  "[Fig7E] I-A-I-E":             "[Final] - I-A-I-E.pdf",
  "[FigS11B] Ciita Exp Level":   "[Final] - Ciita Exp Level.pdf",
  "[FigS11B] H2-Aa Exp Level":   "[Final] - H2-Aa Exp Level.pdf",
  "[FigS11B] H2-Ab1 Exp Level":  "[Final] - H2-Ab1 Exp Level.pdf",
  "[FigS11B] I-A-I-E Exp Level": "[Final] - I-A-I-E Exp Level.pdf",
  "[FigS11A] Ciita (by group)":  "[Final] - Ciita (by group).pdf",
  "[FigS11A] H2-Aa (by group)":  "[Final] - H2-Aa (by group).pdf",
  "[FigS11A] H2-Ab1 (by group)": "[Final] - H2-Ab1 (by group).pdf",
  "[FigS11A] I-A-I-E (by group)":"[Final] - I-A-I-E (by group).pdf",
  "[FigS11A] GOCC_MHC_CLASS_II_PROTEIN_COMPLEX Plot":   "[Final] - GOCC_MHC_CLASS_II_PROTEIN_COMPLEX Plot.pdf",
  "[FigS11A] GOCC_MHC_CLASS_II_PROTEIN_COMPLEX Violin": "[Final] - GOCC_MHC_CLASS_II_PROTEIN_COMPLEX Violin.pdf",
  "[Fig7B-S11] H_IFN":           "[Final] - H_IFN1.pdf",
  "[Fig7B-S11] H_OXPHOS":        "[Final] - H_OXPHOS1.pdf",
  "[Fig7B-S11] H_TNF":           "[Final] - H_TNF1.pdf",
  "[Fig7B-S11] H_TGFB":          "[Final] - H_TGFB1.pdf",
  "[Fig7B-S11] H_E2F":           "[Final] - H_E2F1.pdf",
  "[Fig7B-S11] H_G2M":           "[Final] - H_G2M1.pdf",
 },
}

def png_of(pdf, outdir, tag, dpi=90):
    """Render page 1 of a PDF to PNG; return the relative path or None."""
    if not pdf or not os.path.exists(pdf): return None
    os.makedirs(outdir, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", tag)[:120]
    dest = os.path.join(outdir, stem)
    try:
        subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-r", str(dpi), "-png",
                        "-singlefile", pdf, dest],
                       check=True, capture_output=True, timeout=120)
    except Exception as ex:
        print(f"  render failed for {pdf}: {ex}", file=sys.stderr); return None
    return dest + ".png" if os.path.exists(dest + ".png") else None


def build(exp, rebuilt_dir, dpi):
    e = H.escape
    reb_figs = os.path.join(REB, exp, "02_r_rebuild")
    # rebuilt figs may live in several out* dirs; search them all
    search = []
    for d in sorted(os.listdir(reb_figs)):
        f = os.path.join(reb_figs, d, "figs")
        if os.path.isdir(f) and (rebuilt_dir is None or d == rebuilt_dir):
            search.append(f)
    if not search:
        print(f"{exp}: no rebuilt figs/ found under {reb_figs}", file=sys.stderr)
        return None
    orig_dir = os.path.join(ROOT, exp, "figs")
    out = os.path.join(REB, exp, "02_r_rebuild", "comparison")
    pngdir = os.path.join(out, "png")
    os.makedirs(pngdir, exist_ok=True)

    rows, n_pair, n_missing = [], 0, 0
    for tag, orig_name in PAIRS.get(exp, {}).items():
        rb = None
        for s in search:
            c = os.path.join(s, tag + ".pdf")
            if os.path.exists(c): rb = c; break
        og = os.path.join(orig_dir, orig_name)
        if rb is None and not os.path.exists(og): continue
        a = png_of(og, pngdir, "orig_" + tag, dpi)
        b = png_of(rb, pngdir, "reb_" + tag, dpi)
        if b: n_pair += 1
        else: n_missing += 1
        cell = lambda p, lab: (f'<figure><img src="png/{e(os.path.basename(p))}" alt="{e(lab)}">'
                               f'<figcaption>{e(lab)}</figcaption></figure>'
                               if p else f'<div class="miss">{e(lab)}: not present</div>')
        rows.append(f"""<section id="{re.sub(r'[^a-zA-Z0-9]+','-',tag).strip('-').lower()}">
          <h3>{e(tag)}</h3>
          <div class="pairgrid">{cell(a,'published: '+orig_name)}{cell(b,'rebuilt')}</div>
        </section>""")

    extra = """
.pairgrid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:10px 0 26px}
.pairgrid figure{margin:0;background:var(--panel);border:1px solid var(--line);
  border-radius:8px;padding:10px}
.pairgrid img{width:100%;height:auto;display:block}
.pairgrid figcaption{font-size:11.5px;color:var(--mut);margin-top:7px;word-break:break-word}
.miss{background:var(--chip);color:var(--mut);border:1px dashed var(--line);
  border-radius:8px;padding:26px 14px;font-size:13px;text-align:center}
@media (max-width:900px){.pairgrid{grid-template-columns:1fr}}
h3{margin:26px 0 6px;font-size:16px}
"""
    secs = [(re.sub(r'[^a-zA-Z0-9]+','-',t).strip('-').lower(), t, str(i+1))
            for i, t in enumerate(PAIRS.get(exp, {}))
            if any(os.path.exists(os.path.join(s, t + ".pdf")) for s in search)
            or os.path.exists(os.path.join(orig_dir, PAIRS[exp][t]))]
    groups = [("Panels", secs)]
    html = "\n".join([
        head(f"{exp} figure comparison", extra),
        layout_open(),
        toc(f"{exp} comparison", "published · rebuilt", groups,
            foot=f"{n_pair} pairs rendered<br>{n_missing} rebuilt panels missing<br>"
                 f"generated {datetime.datetime.now():%Y-%m-%d %H:%M}"),
        '<div class="content">',
        f"""<header><div class="kicker">ady3001 · {e(exp)}</div>
        <h1>Published panel vs rebuilt panel</h1>
        <p class="lede">Left is the PDF in <code>{e(exp)}/figs</code> that went into the
        manuscript. Right is what the rebuild script produced. Judge these by eye:
        UMAP rotation, cluster renumbering and permutation p-values move between runs
        without anything being wrong.</p></header>""",
        *rows, "</div>", layout_close(), TOC_JS])
    ok, missing = verify(html)
    if not ok:
        print("dead TOC links:", missing, file=sys.stderr)
    p = os.path.join(out, "comparison.html")
    open(p, "w").write(html)
    print(f"{exp}: wrote {p}  ({n_pair} rebuilt panels, {n_missing} missing)")
    return p


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment", nargs="?", choices=list(PAIRS) + [None])
    ap.add_argument("--rebuilt", default=None, help="which out* dir to use")
    ap.add_argument("--dpi", type=int, default=90)
    a = ap.parse_args()
    for exp in ([a.experiment] if a.experiment else list(PAIRS)):
        build(exp, a.rebuilt, a.dpi)
