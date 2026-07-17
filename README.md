# GrandQC-IDC: Reproducible Quality Control for DICOM Whole-Slide Images

[![tests](https://github.com/ronsong1234/GrandQC_IDC-Validation/actions/workflows/tests.yml/badge.svg)](https://github.com/ronsong1234/GrandQC_IDC-Validation/actions/workflows/tests.yml)

Validation and reproducibility framework for running [GrandQC](https://github.com/cpath-ukk/grandqc)
on NCI Imaging Data Commons (IDC) DICOM pathology slides via `wsidicom`, with matched-SVS
comparisons, a YBR_ICT decoding-safety analysis, and a Zenodo reference-provenance
investigation.

> **This repository validates whether GrandQC produces equivalent quality-control masks
> from original TCGA SVS slides and the corresponding IDC DICOM whole-slide images.**

---

## Findings

1. **SVS–DICOM equivalence.** Running the identical GrandQC pipeline (same code, weights,
   MPP) on IDC DICOM and on the original GDC SVS produces masks that agree at
   **99.957 % whole-image** and **99.988 % within shared tissue** (mean tissue-weighted
   Dice 0.9996 between the two formats; 5-slide set, computed by `src/utils.py`). Inference
   is deterministic — GrandQC rerun on the *same* input is **byte-identical**
   (`np.array_equal == True`) — so the tiny SVS-vs-DICOM difference is a real, negligible
   codec-level effect (±1 grey-level decode floor), not run-to-run noise.

2. **YBR_ICT decoding issue.** IDC serves some TCGA slides as JPEG 2000 **YBR_ICT**.
   OpenSlide 4.0.1 opens these without error but silently fails to apply the color
   transform, feeding GrandQC a mis-colored image and producing an **inverted tissue
   mask** (tissue-weighted Dice collapses ~0.96 → ~0.49). `wsidicom` decodes them
   correctly. In TCGA-BRCA, **29 / 1,104 diagnostic slides (2.6 %) are YBR_ICT** — the
   exposure of any OpenSlide-based pipeline run on IDC pathology data.

3. **Zenodo provenance gap.** The GrandQC authors' **public 2024 code and released
   weights do not reproduce the published Zenodo tissue boundaries.** Run on the original
   SVS they yield the same ~0.70 tissue IoU against Zenodo that our pipeline does, while
   agreeing with our pipeline at 0.99+. The reference-generation procedure is therefore not
   recoverable from the released materials (the public tissue detector is pure `argmax`
   with no threshold, morphology, or post-processing to tune).

See **[CODEBOOK.md](CODEBOOK.md)** for the authoritative model, mask, metric, and metadata
definitions used throughout, and **[docs/findings.md](docs/findings.md)** for the full
write-up.

---

## Workflow

```
IDC DICOM ──wsidicom──┐
                      ├── GrandQC ── mask comparison   (PRIMARY: computational equivalence)
GDC SVS ──OpenSlide───┘
                      └── Zenodo reference             (SECONDARY: provenance analysis)
```

The **fresh SVS mask is the primary computational reference** (the "matched SVS baseline"),
because it holds the pipeline fixed and varies only the input format. The **Zenodo masks are
used only for a separate provenance analysis** — they are *not* treated as ground truth,
because the public GrandQC release does not reproduce them (Finding 3).

---

## Quick start

```bash
conda env create -f environment.yml && conda activate grandqc-idc
# or: pip install -r requirements-lock.txt

# clone the IDC-patched GrandQC fork used by the run scripts, PINNED to the
# validated commit (the branch is a moving target; the commit is what was tested)
git clone https://github.com/fedorov/grandqc.git external/grandqc
git -C external/grandqc checkout 1d9807be7b3a04de2f0cc5d799b55d9fd961f01e

pytest tests/ -q            # 19 tests, ~0.2 s, no data required
```

### Command-line workflow (no notebook required)

```bash
# 1. acquire one slide from each archive
python src/download_idc_dicom.py --barcode TCGA-AC-A23G-01Z-00-DX1 --out-dir data/idc
python src/download_gdc_svs.py  --svs-filename "TCGA-AC-A23G-01Z-00-DX1.<UUID>.svs" \
                                --barcode TCGA-AC-A23G-01Z-00-DX1 --out-dir data/gdc

# 2. run GrandQC on each (same models, MPP; different reader)
python src/run_grandqc_dicom.py --dicom-dir data/idc --output-dir results/dicom/TCGA-AC-A23G
python src/run_grandqc_svs.py   --svs-file data/gdc/TCGA-AC-A23G-01Z-00-DX1.svs \
                                --output-dir results/svs/TCGA-AC-A23G

# 3. compare
python src/compare_masks.py \
    --mask-a results/dicom/TCGA-AC-A23G/mask_qc/TCGA-AC-A23G-01Z-00-DX1_mask.png \
    --mask-b results/svs/TCGA-AC-A23G/mask_qc/TCGA-AC-A23G-01Z-00-DX1.svs_mask.png
```

---

## Notebooks

Each notebook states its purpose, inputs, expected outputs, environment, runtime, and GPU
need at the top, and exports results to CSV/JSON at the end. Every notebook opens with an
**Open in Colab** badge and self-bootstraps there (installs deps, clones this repo for
`src/`, and pins the GrandQC fork to the validated commit) — no local setup needed.

| Notebook | What it does | Status |
|----------|--------------|--------|
| `01_idc_experiment.ipynb` | IDC acquisition + DICOM processing through GrandQC | ✅ Complete |
| `02_svs_dicom_validation.ipynb` | Matched SVS–DICOM validation (primary result) + determinism control | ✅ Complete (5 slides) |
| `03_ybr_ict_prevalence.ipynb` | YBR_ICT prevalence via DICOM-header range reads | ✅ Complete |
| `04_reference_provenance.ipynb` | Zenodo provenance reconstruction with the authors' 2024 code | ✅ Complete |
| `05_stratified_validation.ipynb` | 22-slide stratified validation across codec/scanner/magnification | ⏳ **Pending 22-slide run** — cohort wired, setup cells only; not yet executed at full n |

> **On outputs.** Notebook 05's saved cells are *setup* (cohort selection, download
> plumbing), **not** final 22-slide cohort results — that run has not been executed. The
> headline equivalence numbers come from the 5-slide set (Notebook 02). See
> `docs/limitations.md` §6.

---

## Repository layout

```
src/          command-line pipeline (query, download, run, compare, overlays, utils)
notebooks/    explanatory notebooks (01-05)
config/       cohort CSVs + pipeline_config.yaml
manifests/    model / slide / environment / provenance manifests (with SHA-256)
tests/        pytest guards for the bugs found during the project
results/      summary tables, figures, small example outputs
provenance_experiment/  the Zenodo provenance audit + authors' note + rerun script
docs/         methods, findings, limitations, dashboard integration
```

## Data policy

Large files (SVS, DICOM, `.pth`, Zenodo `.tar`, big masks) are **not committed** — see
`.gitignore`. The `src/` scripts download them on demand; `results/example_outputs/` holds
a few small masks and difference maps for illustration. All heavy artifacts are pinned by
checksum in `manifests/`.

## License & citation

Code under the [MIT License](LICENSE). If you use this work, see [CITATION.cff](CITATION.cff).
GrandQC, the model checkpoints, and the TCGA reference masks are the work of Weng/Tolkach
et al. and are cited there.
