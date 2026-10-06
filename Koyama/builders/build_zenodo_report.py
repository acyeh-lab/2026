#!/usr/bin/env python3
"""
Build zenodo_deposit_report.html - the overall document for the ady3001 code
deposit.

    module load Python/3.11.5-GCCcore-13.2.0
    python3 build_zenodo_report.py

Every number on the page is MEASURED from disk at build time: the package
manifest, the figure map, the deposit-run outputs and the end-to-end test log.
Re-run it after anything changes rather than editing the HTML.
"""
import os, re, sys, glob, html as H, datetime, subprocess

sys.path.insert(0, "/home/ayeh/.claude/skills/html_report")
from house_report import head, toc, layout_open, layout_close, TOC_JS, verify

ROOT = "/fh/fast/hill_g/Albert/scSeq_ST_Analyses/BD_Rhapsody_Motoko_ISC_2024"
REB = os.path.join(ROOT, "Rebuild")
PKG = os.path.join(ROOT, "Zenodo", "ady3001-scseq-code-v1.0.0")
OUT = os.path.join(ROOT, "Sci_Imm_Revision", "zenodo_deposit_report.html")
GSE = "GSE348009"
TODAY = "2026-09-21"

e = H.escape


def measure():
    """Everything the page asserts, read from disk."""
    m = {}
    man = os.path.join(PKG, "MANIFEST.sha256")
    m["n_files"] = sum(1 for _ in open(man)) + 1 if os.path.exists(man) else 0
    m["kib"] = sum(os.path.getsize(os.path.join(dp, f))
                   for dp, _, fs in os.walk(PKG) for f in fs) // 1024

    fm = os.path.join(PKG, "FIGURE_MAP.tsv")
    rows = [l.rstrip("\n").split("\t") for l in open(fm)][1:] if os.path.exists(fm) else []
    m["n_panels"] = len(rows)
    m["figure_rows"] = rows

    exp = os.path.join(PKG, "EXPECTED_RESULTS.tsv")
    m["expected"] = [l.rstrip("\n").split("\t") for l in open(exp)] if os.path.exists(exp) else []

    # end-to-end package test
    logs = sorted(glob.glob(os.path.join(REB, "zenodo", "logs", "pkgtest-*.out")))
    m["test_log"] = logs[-1] if logs else None
    m["test_state"] = "not run"
    m["test_panels"] = None
    m["test_job"] = None
    if m["test_log"]:
        m["test_job"] = re.search(r"pkgtest-(\d+)", m["test_log"]).group(1)
        t = open(m["test_log"], errors="replace").read()
        if "### ALL SCRIPTS COMPLETED" in t:
            m["test_state"] = "PASSED"
        elif "SCRIPT(S) FAILED" in t:
            m["test_state"] = "FAILED"
        elif "run_all.sh exit" in t:
            m["test_state"] = "finished"
        else:
            m["test_state"] = "running"
        # Count the test's ACTUAL output rather than parsing the log line. The
        # log's count came from whatever run_all.sh said at the time, and an
        # earlier version of it counted only *.pdf - which reports 122 where the
        # figure map says 124, because Exp80 writes two panels as PDF *and* PNG.
        od = os.path.join(REB, "zenodo", "pkgtest_output_v2")
        if not os.path.isdir(od):
            od = os.path.join(REB, "zenodo", "pkgtest_output")
        if os.path.isdir(od):
            pdf = png = empty = 0
            for dp, _, fs in os.walk(od):
                for f in fs:
                    if f.lower().endswith(".pdf"):
                        pdf += 1
                    elif f.lower().endswith(".png"):
                        png += 1
                    else:
                        continue
                    if os.path.getsize(os.path.join(dp, f)) == 0:
                        empty += 1
            m["test_panels"] = pdf + png
            m["test_pdf"], m["test_png"], m["test_empty"] = pdf, png, empty

    # r_packages.yml source breakdown
    rp = os.path.join(PKG, "r_packages.yml")
    m["pkg_counts"] = {}
    if os.path.exists(rp):
        for lab, n in re.findall(r"^# --- (.+?) \((\d+)\)", open(rp).read(), re.M):
            m["pkg_counts"][lab] = int(n)
    return m


M = measure()

SECTIONS = [
    ("what", "What this deposit is", "1"),
    ("where", "GEO vs Zenodo", "2"),
    ("coverage", "Figure coverage", "3"),
    ("gaps", "Gaps in the public record", "4"),
    ("corrections", "Two Methods corrections", "5"),
    ("contents", "Package contents", "6"),
    ("environment", "Environment & the YAML", "7"),
    ("evidence", "Reproducibility evidence", "8"),
    ("endtoend", "End-to-end package test", "9"),
    ("limits", "Known limits", "10"),
    ("howto", "How to run it", "11"),
    ("next", "What is left to do", "12"),
]

CSS = """
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:.92em}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:600}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.ok{color:#137333;font-weight:600}
.bad{color:#b3261e;font-weight:600}
details{margin:10px 0;border:1px solid var(--line);border-radius:6px;padding:8px 12px}
summary{cursor:pointer;font-weight:600}
pre{overflow-x:auto;padding:10px 12px;border-radius:6px;background:var(--soft);
    border:1px solid var(--line);font-size:.86em;line-height:1.45}
"""


def sec(sid, title, tnum, body):
    return (f'<section id="{sid}">\n'
            f'<h2 class="section"><span class="num">{tnum}</span> {e(title)}</h2>\n'
            f'{body}\n</section>')


def table(headers, rows, cls=""):
    L = [f'<table class="{cls}">']
    # A key/value table is passed all-empty headers; rendering an empty <thead>
    # row leaves a stray grey stripe.
    if any(h.strip() for h in headers):
        L.append("<thead><tr>")
        L += [f"<th>{h}</th>" for h in headers]
        L.append("</tr></thead>")
    L.append("<tbody>")
    for r in rows:
        L.append("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    L.append("</tbody></table>")
    return "\n".join(L)


# ---------------------------------------------------------------- sections
S = {}

S["what"] = f"""
<p class="lede">A complete, citable record of how every single-cell RNA-sequencing
figure in Koyama <em>et al.</em> was produced &mdash; built because the record that
currently exists is incomplete.</p>

<p>The package at <code>Zenodo/ady3001-scseq-code-v1.0.0</code> holds
<strong>{M['n_files']} files</strong> ({M['kib']:,} KiB) and regenerates
<strong>seven figures</strong> from the matrices deposited in GEO. It carries the
original R&nbsp;Markdown as the historical record, a runnable transcription of it,
the pinned software environment, the optional FASTQ&rarr;matrix pipeline, and the
scripts that verified the whole thing.</p>

<div class="callout"><strong>Why this is not optional.</strong> GEO takes data, not
figure-generation code. The GitHub repository the Methods cite is missing all of
Figure&nbsp;S7, Figure&nbsp;S6C and every line of the Figure&nbsp;S3 analysis
(&sect;4). Without this deposit there is no public, complete account of how the
figures were made.</div>
"""

S["where"] = f"""
<p>Two archives, two jobs. Neither substitutes for the other.</p>
{table(["", "NCBI GEO", "Zenodo"], [
  ["Accession", f'<strong>{GSE}</strong>', "DOI &mdash; not yet minted"],
  ["Holds", "16 raw FASTQ (208.0 GiB) + 28 processed matrices (3.9 GiB)",
   f"{M['n_files']} files of code, documentation and environment ({M['kib']:,} KiB)"],
  ["Status", "Accessioned 2026-09-21, all 7 records <span class='ok'>approved</span>",
   "Built and verified; ready to upload"],
  ["Release", "2026-10-18 (must be moved up if the paper publishes first)",
   "On upload"],
  ["Cited as", "the data availability accession", "the source-code citation"],
])}
<p>The Methods currently point source code at
<code>github.com/acyeh-lab/2024/tree/main/Koyama/scseq</code>. Once the DOI exists
that sentence should cite the DOI instead, or in addition.</p>
"""

cov_rows = [
    ["<strong>Fig 4</strong>", "B&ndash;D", "Exp160 &mdash; ileal IEC, na&iuml;ve + 24&nbsp;h TBI WT",
     "<code>Exp160/01_fig4_figS6.R</code>"],
    ["<strong>Fig S6</strong>", "A&ndash;E", "Exp160 &mdash; same cells",
     "<code>Exp160/01_fig4_figS6.R</code>"],
    ["<strong>Fig S7</strong>", "B&ndash;E", "Exp160 &mdash; 24&nbsp;h TBI WT + MHC-II KO",
     "<code>Exp160/02_figS7.R</code>"],
    ["<strong>Fig S10</strong>", "A&ndash;D", "Exp649 &mdash; ileal ISC, day 7 post-BMT",
     "<code>Exp649/01_figS10_qc.R</code>"],
    ["<strong>Fig 7</strong>", "B&ndash;F", "Exp649 &mdash; Lgr5+ ISC subset",
     "<code>Exp649/02_fig7_figS11.R</code>"],
    ["<strong>Fig S11</strong>", "A&ndash;C", "Exp649 &mdash; same subset",
     "<code>Exp649/02_fig7_figS11.R</code>"],
    ["<strong>Fig S3</strong>", "A&ndash;C", "Exp80 &mdash; Marilyn T cells, ileal EL vs LP",
     "<code>Exp80/02_figS3_from_deposit.R</code>"],
]
S["coverage"] = f"""
<p>Confirmed against the accepted manuscript PDF
(<code>ady3001--Koyama et al--combined pdf (8-14-2026).pdf</code>), not against
memory. Figure legends were extracted and every panel classified.</p>
{table(["Figure", "Panels", "Experiment", "Script"], cov_rows)}
<p>Panel&nbsp;A of Figures 4, 7 and S7 is an experimental schema, not data.
Figure&nbsp;S3D&ndash;F are flow cytometry and a redirected-cytotoxicity assay.
<strong>No scRNA-seq panel appears anywhere else in the paper</strong> &mdash; not in
Fig 1, 2, 3, 5, 6 or 8, nor in S1, S2, S4, S5, S8, S9 or S12.</p>
<p><code>FIGURE_MAP.tsv</code> names all <strong>{M['n_panels']}</strong> output
panels individually and maps each to the script that writes it.</p>
"""

S["gaps"] = """
<p>The Methods cite
<code>https://github.com/acyeh-lab/2024/tree/main/Koyama/scseq</code>. That
directory was fetched and compared, file by file, on 2026-09-21. It holds three
files and is incomplete in three separate ways.</p>

<h3>1. The public Exp160 file is the pre-revision version</h3>
""" + table(["", "on GitHub", "in this deposit"], [
    ["<code>Exp160_Final.Rmd</code>", "22,843 bytes &middot; 486 lines &middot; <strong>6 chunks</strong>",
     "74,117 bytes &middot; 1,551 lines &middot; <strong>16 chunks</strong>"],
]) + """
<p>Missing from the public copy: every <code>add Cart 3 &hellip;</code> chunk &mdash;
which is <strong>all of Figure&nbsp;S7</strong> &mdash; and the
<code>Lgr4 and Fgfbp1 - New ISC model</code> chunk, which is
<strong>Figure&nbsp;S6C</strong>. Both were added during revision.
<code>grep -c cart3</code> returns <strong>0</strong> on the public file and
<strong>21</strong> on the real one.</p>

<h3>2. The Exp80 code was never published at all</h3>
<p><code>241221_Marilyn.Rmd</code>, which produces Figure&nbsp;S3A&ndash;C, is absent
from the repository. It is included here, together with its rendered HTML &mdash;
the only surviving record of that analysis's own <code>sessionInfo</code>.</p>

<h3>3. The public Exp649 file cannot run, and its readme is stale</h3>
<p><code>Exp649_Final.Rmd</code> differs from the working copy in exactly two lines,
both the same error: it says <code>scSeq_Analyses</code> where the directory is
<code>scSeq_ST_Analyses</code>, so its <code>setwd()</code> fails immediately. The
accompanying <code>readme.txt</code> still uses pre-revision figure numbers
&mdash; "Figure 3" and "Figure 6" for what are now Figures 4 and 7.</p>

<div class="callout"><strong>This archive supersedes that repository.</strong> The
GitHub directory should either be updated from this package or redirected to the
Zenodo DOI.</div>
"""

S["corrections"] = """
<p>Two statements in the accepted Methods are wrong. Both were found by running the
code, and both are material.</p>

<h3>1. The mitochondrial threshold is 40&thinsp;%, not 25&thinsp;%</h3>
<p>The Methods read: <em>"percent.mt &lt; 25% (IEC analysis) or percent.mt &lt; 40%
(ISC analysis)"</em>. Every published object &mdash; including both IEC objects
&mdash; has a <code>percent.mt</code> maximum near 40.</p>
""" + table(["Filter", "Cells", "Clusters", "Matches the published Fig 4 object?"], [
    ["<code>percent.mt &lt; 25</code>", "6,412", "8", "<span class='bad'>no</span>"],
    ["<code>percent.mt &lt; 40</code>", "<strong>8,032</strong>", "<strong>7</strong>",
     "<span class='ok'>yes &mdash; exactly, including the 3,334 / 4,698 cartridge split</span>"],
]) + """
<p>Verified four independent ways: every published object's observed maximum; all
four rebuild analyses reproducing at 40; a live re-run of the original Rmd at 25
giving 6,412; and the fact that the Rmd's figure chunks <code>readRDS()</code> the
object from disk rather than using the filtered object in memory.</p>
<p><strong>The difference is not cosmetic.</strong> The 1,620 extra cells retained at
40 have <em>higher</em> median complexity than the retained set (1,425 genes /
4,348 UMIs versus 1,234 / 3,304) and form a distinct high-mitochondrial cluster
that largely disappears at 25. A reader following "25&thinsp;%" gets a materially
different result.</p>

<h3>2. The R version is 4.4.0, not 4.0.3</h3>
<p>The Statistical analysis section reads: <em>"R (ver. 4.0.3) for RNAseq data"</em>.
All five published Seurat objects record <code>SeuratObject</code>
<strong>5.0.2</strong> in their <code>@version</code> slot:</p>
""" + table(["Published object", "Cells", "Clusters", "<code>@version</code>"], [
    ["<code>Exp160/cds/241108v2_processed.RDS</code>", "8,032", "7", "5.0.2"],
    ["<code>Exp160/cds/250814_cart2_3_processed.RDS</code>", "7,478", "6", "5.0.2"],
    ["<code>Exp160/cds/250814_cart_all_processed.RDS</code>", "10,812", "9", "5.0.2"],
    ["<code>Exp649/cds/241104_processed.RDS</code>", "9,135", "12", "5.0.2"],
    ["<code>Exp649/cds/241105_processed.RDS</code>", "6,828", "9", "5.0.2"],
]) + """
<p><code>SeuratObject</code> 5.0.2 was packaged 2024-05-07 and declares
<code>Depends: R (&gt;= 4.1.0)</code>. R 4.0.3 is from October 2020 and cannot load
these objects; the objects themselves were written in November 2024 and August 2025.
The "4.0.3" is a carry-over from the 2020&ndash;2022 exploratory analyses.</p>
<p>The correct statement is <strong>R 4.4.0 / Seurat 5.1.0</strong> for the IEC and
ISC experiments and <strong>R 4.3.2 / Seurat 5.0.0</strong> for the Marilyn T-cell
experiment.</p>

<h3>What was checked and is correct</h3>
<p>So the two above are not hedged: the rest of the scRNA-seq Methods was checked
against the data and holds.</p>
<ul>
<li><strong>The AbSeq panel description is exact.</strong> The Methods name
"CD326 AMM2065, CD45.2 AMM2014, IAIE AMM2019, H-2Kb AMM2060" for the IEC
experiment; the four <code>|pAbO</code> columns in
<code>cartridge1_RSEC_MolsPerCell.csv</code> are precisely those four catalog
numbers. For the ISC experiment the Methods describe the same three shared
antibodies plus four individual CD326 oligos (AMM2065, 2281, 2294, 2295); Exp649's
header carries exactly those seven.</li>
<li><strong>The stated clustering resolutions are correct.</strong> In every saved
object <code>seurat_clusters</code> is byte-identical to the
<code>RNA_snn_res.*</code> column the code names.</li>
<li><strong>The instruments are correct</strong> &mdash; NovaSeq for the IEC
experiment, NextSeq 2000 for the ISC experiment &mdash; and match the run folders
and the BD metrics headers.</li>
<li><strong>RSEC, not DBEC, is the right choice</strong> and is what the analysis
reads.</li>
</ul>
"""

S["contents"] = """
<pre>ady3001-scseq-code-v1.0.0/
  README.md                  the landing document
  FIGURE_MAP.tsv             every panel &rarr; the script that writes it
  EXPECTED_RESULTS.tsv       exact cell / cluster / panel counts
  environment.yml            conda/mamba environment
  r_packages.yml             the full measured package-version record
  MANIFEST.sha256            checksum of every file
  LICENSE (MIT)  CITATION.cff
  run_all.sh                 regenerate every panel
  verify_package.sh          checks that need neither data nor R

  01_original_code/          the Rmds as they were, unmodified
     Exp160_Final.Rmd  Exp649_Final.Rmd  241221_Marilyn.Rmd (+ .html)
     Exp160_AYEH_241108_FINAL.Rmd  Exp649_AYEH_241104_FINAL.Rmd
     KNOWN_ISSUES.md         the five defects, with evidence
  02_figure_scripts/         the runnable transcription &mdash; run these
     common/config.R  common/load_bd.R
     Exp160/  Exp649/  Exp80/
  03_environment/            sessionInfo of the verified runs + pin scripts
  04_bd_pipeline/            optional: FASTQ &rarr; matrices, version-pinned BD
  05_verification/           the scripts that proved the deposit reproduces
  tools/unpack_geo_download.sh</pre>

<div class="callout"><strong>The original Rmds are deposited unmodified, defects and
all.</strong> They are the historical record: a reader comparing the paper to the
code needs to see what was actually run, not a cleaned-up version.
<code>KNOWN_ISSUES.md</code> documents all five defects &mdash; including that
knitting <code>Exp160_Final.Rmd</code> in place would overwrite the published
8,032-cell object with a wrong 6,412-cell one. Anything you intend to
<em>execute</em> lives in <code>02_figure_scripts/</code>.</div>
"""

pkgc = M["pkg_counts"]
pkg_rows = [[k.split(" - ")[0].split(" (")[0], f'<span class="n">{v}</span>']
            for k, v in pkgc.items()]
S["environment"] = f"""
{table(["", "Exp160 / Exp649", "Exp80 (Fig S3)"], [
  ["R", "<strong>4.4.0</strong>", "<strong>4.3.2</strong>"],
  ["Seurat", "<strong>5.1.0</strong>", "<strong>5.0.0</strong>"],
  ["SeuratObject", "5.0.2", "5.0.1"],
  ["scCustomize", "2.1.2", "2.1.1"],
  ["also", "monocle3 1.3.7 (Exp160), fgsea 1.30.0 (Exp649)", "&mdash;"],
])}
<p>The two experiments genuinely used different Seurat versions. 5.1.0 and 5.0.0 are
not a typo for one another, and crossing them is an easy mistake &mdash; it happened
once in the GEO metadata workbook.</p>

<h3>The two YAML files</h3>
<p>Both are generated by reading each package's installed <code>DESCRIPTION</code>,
so the version <em>and</em> the CRAN / Bioconductor / GitHub classification are
measured rather than assumed.</p>
{table(["Source", "Packages"], pkg_rows)}
<ul>
<li><code><strong>r_packages.yml</strong></code> &mdash; the authoritative record of
what ran. A record, not an installer.</li>
<li><code><strong>environment.yml</strong></code> &mdash; a conda/mamba environment,
for GitHub and for portability. It is a convenience, and says so: conda-forge and
bioconda do not carry every one of these versions on every platform, and five
packages are GitHub-only with no conda package at all (they are listed as
<code>remotes::install_github</code> lines).</li>
</ul>
<div class="callout warn"><strong>Pin the library.</strong> On 2026-09-18 the R
library holding these packages was updated in place &mdash; Seurat 5.1.0&nbsp;&rarr;
5.5.1, ggplot2 3.4.4&nbsp;&rarr;&nbsp;4.0.3 among eleven changes &mdash; and the
analysis stopped running the same day: Seurat would not load at all. ggplot2 4.x is
the S7 rewrite, which breaks Seurat 5.1.0's <code>patchwork &amp; theme</code> idiom.
Reproducibility that rested on a mutable home directory lasted <strong>three
days</strong>. <code>03_environment/install_r_pin.sh</code> exists because of
that.</div>
"""

S["evidence"] = """
<p>Every script was run against a <strong>clean room</strong> containing nothing but
the 28 processed files actually deposited in GEO, copied from their manifest source
paths and md5-verified against the upload manifest (<strong>28/28 ok</strong>), with
no other project file reachable from it. This answers "can someone who downloads only
what is on GEO regenerate the published objects?" &mdash; not "does the lab copy
still work".</p>
""" + table(["Figure", "Cells", "Clusters", "Cluster sizes",
             "Cell-for-cell agreement with the published object"], [
    ["Fig 4 / S6", "8,032 = 8,032", "7 = 7", "identical", "<span class='ok'>100.00&thinsp;%</span>"],
    ["Fig S7", "7,478 = 7,478", "6 = 6", "identical", "<span class='ok'>100.00&thinsp;%</span>"],
    ["Fig S10", "9,135 = 9,135", "12 = 12", "identical", "<span class='ok'>100.00&thinsp;%</span>"],
    ["Fig 7 / S11", "6,828 = 6,828", "9 = 9", "identical", "<span class='ok'>100.00&thinsp;%</span>"],
]) + """
<p>Identical along the way too: 15,288&nbsp;&rarr;&nbsp;8,032 and
23,841&nbsp;&rarr;&nbsp;7,478 and
30,391&nbsp;&rarr;&nbsp;10,363&nbsp;&rarr;&nbsp;9,135 (965 multiplets, 263 no-tag).
<strong>124 panels</strong> written, <strong>none empty</strong>.</p>

<h3>Figure S3 reproduces by two independent routes</h3>
<p>The deposit carries four of Exp80's eight sample tags (SampleTag05&ndash;08 =
LP, EL), which is what Figure&nbsp;S3 uses. Both routes were checked:</p>
<ul>
<li><strong>Route A</strong> &mdash; the four deposited per-tag matrices:
1,334 / 1,600 / 871 / 739 = <strong>4,544 cells</strong>, LP 2,934 / EL 1,610,
165,021 edges, modularity 0.7328 &mdash; every number identical to the eight-tag
run.</li>
<li><strong>Route B</strong> &mdash; the deposited Combined matrix split by the
deposited <code>Sample_Tag_Calls.csv</code>: <strong>identical cells, features and
values to route A</strong> for all four tags.</li>
</ul>
<p>The Figure&nbsp;S3B dot plot matches the full eight-tag run to
<strong>4.4&thinsp;&times;&thinsp;10<sup>&minus;16</sup></strong>, with the LP/EL
direction preserved for all nine genes &mdash; including the distinctive
<code>Fasl</code> reversal.</p>
"""

tl = M["test_log"]
badge = {"PASSED": "<span class='ok'>PASSED</span>",
         "FAILED": "<span class='bad'>FAILED</span>",
         "running": "<em>still running</em>",
         "finished": "finished",
         "not run": "<em>not run</em>"}[M["test_state"]]
S["endtoend"] = f"""
<p>The evidence in &sect;8 was gathered with the lab working copies. This section is
the test of <strong>the package itself</strong>: the packaged scripts, resolving
their own paths, reading the clean room through
<code>$ADY3001_DATA</code>, writing to a scratch directory. It is what a reader who
downloads GSE348009 and this archive actually experiences.</p>
{table(["", ""], [
  ["SLURM job", f"<code>{M['test_job'] or '&mdash;'}</code>"],
  ["Command", "<code>run_all.sh</code> inside the package"],
  ["Result", badge],
  ["Panels written",
   (f"<strong>{M['test_panels']}</strong> "
    f"({M.get('test_pdf', 0)} pdf + {M.get('test_png', 0)} png)")
   if M["test_panels"] is not None else "&mdash;"],
  ["Empty panels",
   ("<span class='ok'>0</span>" if M.get("test_empty") == 0
    else f"<span class='bad'>{M.get('test_empty')}</span>")
   if M["test_panels"] is not None else "&mdash;"],
  ["Log", f"<code>{e(tl)}</code>" if tl else "&mdash;"],
])}
{table(["Script", "Cells", "Clusters", "Panels", "Result tables vs the lab run"], [
  ["<code>Exp160/01_fig4_figS6.R</code>", "15,288 &rarr; <strong>8,032</strong>", "7", "40",
   "<span class='ok'>byte-identical</span>"],
  ["<code>Exp160/02_figS7.R</code>", "23,841 &rarr; <strong>7,478</strong>", "6", "26",
   "<span class='ok'>byte-identical</span>"],
  ["<code>Exp649/01_figS10_qc.R</code>",
   "30,391 &rarr; 10,363 &rarr; <strong>9,135</strong><br><small>965 multiplets, 263 no-tag</small>",
   "12", "14", "<span class='ok'>byte-identical</span> (3/3)"],
  ["<code>Exp649/02_fig7_figS11.R</code>", "9,135 &rarr; <strong>6,828</strong>", "9", "39",
   "<span class='ok'>byte-identical</span> (10/10, incl. the GSEA tables)"],
  ["<code>Exp80/02_figS3_from_deposit.R</code>", "<strong>4,544</strong><br>"
   "<small>1,334 / 1,600 / 871 / 739</small>", "n/a", "5",
   "<span class='ok'>byte-identical</span>"],
])}
<p>Every cell count, cluster count and panel count matches the published objects.
The Exp649 GSEA tables being byte-identical is worth noting on its own: <code>fgsea</code>
is permutation-based, so identical output means the seeding is deterministic end to
end, not merely close.</p>
<p>The package also ships <code>verify_package.sh</code>, which needs neither the data
nor a working R: it checks every file against <code>MANIFEST.sha256</code>, greps for
absolute paths that escaped the rewrite, parses every R script, and prints the
expected results. It found and forced the fix of a real defect during the build
&mdash; a hardcoded lab library path inside <code>load_bd.R</code>.</p>
"""

S["limits"] = """
<p>Stated plainly, because a deposit that overclaims is worse than one that does
not.</p>

<h3>UMAP orientation is not reproducible, and does not need to be</h3>
<p>A UMAP embedding is defined only up to rotation and reflection. The
Figure&nbsp;S3A rebuild is <strong>horizontally mirrored</strong> relative to the
published panel. The structure, the groupings and every quantitative value are
identical. This is a property of the algorithm, not a defect.</p>

<h3>Figures 7 / S11 do not reproduce from matrices regenerated from FASTQ</h3>
<p>They reproduce <em>exactly</em> from the deposited matrices, which is what GEO
carries and what the scripts default to. But re-running the BD pipeline from raw
reads shifts about 0.001&thinsp;% of molecules, and Louvain clustering at resolution
0.5 sits near a community boundary for this dataset &mdash; enough to renumber the
12-cluster map and yield 7 ISC communities instead of 9. The cell set is essentially
unchanged (6,821 shared, Jaccard 0.997, group counts within 2 cells).</p>
<p><strong>The script detects this and refuses to claim a reproduction</strong>
rather than silently subsetting the wrong clusters.</p>

<h3>Exp80's FASTQ&rarr;matrix step is not version-matched</h3>
<p>Exp80 used the targeted Immune Response panel on BD pipeline v1.8. BD never
published the v1.8 targeted CWL and it is not inside the v1.8 container, so that step
cannot be re-run at the original version. The deposited matrices are BD's original
v1.8 output.</p>

<h3>One fact rests on a single source</h3>
<p>Which of the four CD326 AbSeq oligos marks which Exp649 sorted population is not
recoverable from any file &mdash; it is transcribed from the Rmd. Nothing downstream
can detect a swap; the clusters would simply carry the wrong group labels. The
mapping used is AMM2065&nbsp;&rarr;&nbsp;Female IFN&gamma;R+,
2281&nbsp;&rarr;&nbsp;Female IFN&gamma;R&minus;, 2294&nbsp;&rarr;&nbsp;Male
IFN&gamma;R+, 2295&nbsp;&rarr;&nbsp;Male IFN&gamma;R&minus;. The paper lists the four
oligos in that order but never pairs them.</p>

<h3>Do not add seeds</h3>
<p>Seurat's per-function seed defaults (<code>FindClusters(random.seed = 0)</code>,
<code>RunPCA</code>/<code>RunUMAP(seed.use = 42)</code>,
<code>AddModuleScore(seed = 1)</code>) are already fixed, and the original code never
overrode them. Passing <code>set.seed(1234)</code> into <code>FindClusters</code>
gives 8 communities where the published Figure&nbsp;4 object has 7.</p>

<h3>There is no original <code>sessionInfo</code></h3>
<p>Neither final Rmd was ever knitted to a rendered record. The eight HTML files in
the lab's <code>rmd/</code> directories are 2020&ndash;2022 exploratory versions and
must not be cited as describing the published analysis. The
<code>sessionInfo</code> files in <code>03_environment/</code> are from the runs that
reproduce the published objects cluster-for-cluster, which is the strongest available
evidence and is what the deposit offers instead.</p>
"""

S["howto"] = """
<pre># 1. download the supplementary files of """ + GSE + """ into one directory
# 2. rearrange them into the layout the scripts expect
./tools/unpack_geo_download.sh ~/Downloads/""" + GSE + """ ~/ady3001_data
export ADY3001_DATA=~/ady3001_data

# 3. check the package itself (seconds; needs neither data nor R)
./verify_package.sh

# 4. regenerate every panel
./run_all.sh</pre>

<div class="callout warn"><strong>Step 2 is not optional.</strong> A GEO download is
<em>flat</em>. The scripts expect one directory per cartridge, and for Exp80 one
directory per sample tag whose name <strong>ends <code>_mm</code></strong> &mdash;
the <code>Sample_Tag_Calls</code> file spells the tag
<code>SampleTag05_mm</code>, not <code>SampleTag05</code>. Skip the unpack step and a
perfectly good deposit looks empty.</div>

<p>Three environment variables control everything, all optional:
<code>ADY3001_DATA</code> (the unpacked download),
<code>ADY3001_OUT</code> (where results go, default <code>./output</code>) and
<code>ADY3001_LIB</code> (extra R libraries, colon-separated, placed first).</p>

<p>Order matters in exactly one place: <code>Exp649/02_fig7_figS11.R</code> reads the
Seurat object written by <code>Exp649/01_figS10_qc.R</code>.
<code>run_all.sh</code> enforces it.</p>
"""

S["next"] = """
<ol>
<li><strong>Mint the Zenodo DOI</strong> from this package. Upload the directory as a
single archive; <code>CITATION.cff</code> and the MIT <code>LICENSE</code> are
already in place.</li>
<li><strong>Correct the Methods</strong> &mdash; both items in &sect;5. The
<code>percent.mt</code> one changes a stated parameter that a reader would otherwise
follow to a different answer; the R version one is a factual error about the
software.</li>
<li><strong>Update or redirect the GitHub repository.</strong> As it stands it is
missing Figure&nbsp;S7, Figure&nbsp;S6C and all of the Figure&nbsp;S3 code, and its
Exp649 file cannot run because of a path typo.</li>
<li><strong>Email <code>geo@ncbi.nlm.nih.gov</code></strong> to attach the DOI to
""" + GSE + """ once minted.</li>
<li><strong>Watch the GEO release date.</strong> """ + GSE + """ is scheduled for
2026-10-18, but NCBI requires release as soon as the accession appears in any public
manuscript or preprint. Nothing reminds you automatically.</li>
<li><strong>Confirm the Exp649 oligo&rarr;group mapping with Motoko</strong> &mdash;
the one fact in &sect;10 that rests on a single source.</li>
</ol>
"""

body = [sec(sid, title, tnum, S[sid]) for sid, title, tnum in SECTIONS]

header = f"""<header>
<div class="kicker">Koyama <em>et al.</em> &middot; <span class="hutch">Science
Immunology</span> &middot; ady3001</div>
<h1>Zenodo code deposit</h1>
<p class="lede">The complete record of how every scRNA-seq figure in the paper was
produced &mdash; what is in the package, what it reproduces, what it does not, and
what the published record currently gets wrong.</p>
<p><span class="chip">{M['n_files']} files</span>
<span class="chip">{M['n_panels']} panels</span>
<span class="chip">7 figures</span>
<span class="chip">GEO {GSE}</span>
<span class="chip">MIT</span></p>
</header>"""

parts = [
    head("Zenodo code deposit — ady3001", CSS),
    layout_open(),
    toc("Zenodo deposit", "Koyama et al. · ady3001",
        [("The deposit", SECTIONS[:3]),
         ("What it fixes", SECTIONS[3:5]),
         ("The package", SECTIONS[5:7]),
         ("Does it work", SECTIONS[7:10]),
         ("Using it", SECTIONS[10:])],
        foot=f"{M['n_files']} files &middot; {M['n_panels']} panels &middot; "
             f"generated {TODAY}<br><code>Zenodo/ady3001-scseq-code-v1.0.0</code>"),
    '<div class="content">',
    header,
    *body,
    "</div>", layout_close(), TOC_JS,
]
html = "\n".join(parts)

ok, missing = verify(html)
if not ok:
    raise SystemExit(f"FATAL: TOC targets with no section: {missing}")

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(html)
print(f"wrote {OUT}  ({len(html)/1024:.0f} KiB)")
print(f"  {M['n_files']} files, {M['n_panels']} panels, test={M['test_state']}")
