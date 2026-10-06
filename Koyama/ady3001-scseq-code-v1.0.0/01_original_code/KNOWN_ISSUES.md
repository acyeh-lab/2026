# Known issues in the original R Markdown

These files are the **historical record**: the code as it stood when the
published figures were made. **One value was corrected** - see item 1 - and
everything else is deposited as it was, defects included, because a reader
comparing the paper to the code needs to see what was actually run.
**They will not knit from a clean session.** Use
`../02_figure_scripts/` for anything you intend to execute.

Each defect below was found by running the code, not by reading it.

---

## 1. `percent.mt` corrected from 25 to 40 (line 157) - CHANGED 2026-10-06

The Fig 4 / S6 filter in `Exp160_Final.Rmd` **now reads `percent.mt < 40`**.
Until 2026-10-06 it read `25`. That was a stale edit, not the threshold that
produced the figures: 25 keeps **6,412 cells**, whereas the object the published
figure was made from, `241108v2_processed.RDS`, holds **8,032 cells in 7
clusters** with a `percent.mt` maximum of 39.994 - and the Rmd's own inline
comment on that very line has always read "This gives us 8,032 samples".

**40 is the threshold that was actually used**, the same as Fig S7, S10 and S11.
Confirmed five independent ways:

- every object the figures are made from maxes near 40. (One object in the
  same folder, `241108_processed.RDS`, does max at 24.97 with 6,412 cells and 6
  clusters - that is the SUPERSEDED first pass at 25, written the same day.
  Neither Rmd ever wrote it: both save and read `241108v2`. It is the exception
  that proves which object is which, not a counter-example.)
- all four rebuild analyses reproduce the published objects at 40
- re-running the original Rmd at 25 gives 6,412 cells, not the 8,032 the Rmd's
  own inline comment claims
- the three other filter calls in the same file (lines 623, 827 and 1182) have
  always read 40, with comments giving 2,782 / 10,812 / 7,478 cells that match
  their published objects exactly. The file disagreed only with itself, on this
  one line.
- the first author confirms that 40 is what was run

The Rmd's YAML is dated 2025-08-14 while the object it reads was written
2024-11-11, so the `25` was introduced roughly nine months *after* the figures
were made. The same stale value stood in `Exp160_AYEH_241108_FINAL.Rmd`, which
saves and reads that same `241108v2` object, and was corrected there too.

**The difference is not cosmetic**, which is why it was corrected rather than
merely annotated. 40 keeps 20.2% more cells than 25 (8,032 against 6,412) and
yields the published **7** clusters, where re-running at 25 gives 8. The extra
cells are not debris - their median complexity (1,425 genes / 4,348 UMIs) is
*higher* than the retained set (1,234 / 3,304) - and they concentrate into a
distinct high-mitochondrial island that largely disappears at 25.

> The manuscript Methods were corrected to **40% for both** the IEC and the ISC
> analyses.

## 2. `DefaultAssay(seu_sub) <- "RNA"` precedes the creation of `seu_sub` (line 154)

Line 154 sets the default assay on `seu_sub`; line 157 creates it. On a clean
run this errors immediately. It only ever worked because `seu_sub` was left over
in an interactive session.

## 3. `test0_1` is never assigned (`Exp160_Final.Rmd`, volcano for Fig S7E)

The volcano data frame is built as

    volcano_0_2 <- data.frame(cbind(rownames(test0_2),
                                    test0_2$p_val_adj < 0.05,
                                    test0_2$avg_log2FC,
                                    test0_1$p_val))        # <- test0_1

`test0_1` appears nowhere in the Exp160 corpus, so this raises
`object 'test0_1' not found`. Every other column comes from `test0_2`
(cluster 0 vs cluster 2); the packaged script takes the p-value column from
`test0_2` as well.

## 4. `order_cells(cds)` is interactive (lines 478 and 501)

Called with no arguments, monocle3's `order_cells` opens a Shiny window and
blocks forever in a non-interactive run. The Fig S6B legend states the stem-cell
cluster was used as the root node, so the packaged script selects that root
programmatically.

## 5. Knitting these files in place is DESTRUCTIVE

`Exp160_Final.Rmd` writes `saveRDS(..., "241108v2_processed.RDS")` straight into
the analysis directory, and about forty `pdf()` calls overwrite the published
figure PDFs. `Exp649_Final.Rmd` overwrites two more objects.

Running `Exp160_Final.Rmd` unmodified would overwrite the published 8,032-cell
object with a **wrong** 6,412-cell one, because of defect 1.

**Never knit these in a directory you care about.** Redirect the output
directories first.

---

## What is NOT wrong

- **The stated resolutions are correct.** In every saved object
  `seurat_clusters` is byte-identical to the `RNA_snn_res.*` column the Rmd
  names.
- **The seeds are correct.** Seurat's per-function seed defaults
  (`FindClusters(random.seed = 0)`, `RunPCA`/`RunUMAP(seed.use = 42)`,
  `AddModuleScore(seed = 1)`) are already fixed and the Rmds never override
  them. Do **not** "improve" this by passing `set.seed(1234)` into those calls -
  at resolution 0.15 it gives 8 communities where the published Fig 4 object has
  7.

---

## Relationship to the GitHub repository cited in the Methods

The Methods cite `https://github.com/acyeh-lab/2024/tree/main/Koyama/scseq`.
As of 2026-09-21 that directory holds three files and is **incomplete**:

| | on GitHub | here |
|---|---|---|
| `Exp160_Final.Rmd` | 486 lines, **7 chunks** | 1,551 lines, **17 chunks** |
| `Exp649_Final.Rmd` | 829 lines | 829 lines (identical but for a path typo) |
| `241221_Marilyn.Rmd` (Exp80, Fig S3) | **absent** | present |

The public `Exp160_Final.Rmd` is the pre-revision version. Missing from it:

- every `add Cart 3 ...` chunk - i.e. **all of Figure S7**
- `Lgr4 and Fgfbp1 - New ISC model` - **Figure S6C**

The public `Exp649_Final.Rmd` differs in two lines, both the same path error:
it says `scSeq_Analyses` where the directory is `scSeq_ST_Analyses`, so its
`setwd()` cannot succeed. Its `readme.txt` also uses the pre-revision figure
numbers ("Figure 3" and "Figure 6" for what are now Figures 4 and 7).

**This archive supersedes that repository.**
