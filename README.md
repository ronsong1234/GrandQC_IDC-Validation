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
   Dice 0.9996 between the two formats; 5-slide set, computed by `grandqc_idc.metrics`). Inference
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
pip install -e ".[all]"          # installs the grandqc_idc package + all extras
# or, lightweight (metrics/tests only): pip install -e .
# or the exact pinned env:         pip install -r requirements-lock.txt && pip install -e . --no-deps

# clone the IDC-patched GrandQC fork used for inference, PINNED to the validated
# commit (the branch is a moving target; the commit is what was tested)
git clone https://github.com/fedorov/grandqc.git external/grandqc
git -C external/grandqc checkout 1d9807be7b3a04de2f0cc5d799b55d9fd961f01e

pytest tests/ -q                 # 20 tests, ~1 s, no data required
```

### Command-line tools

Installing the package registers three console scripts:

```bash
# compare two masks (whole-image / within-tissue agreement, IoU, Dice)
grandqc-compare --mask-a results/dicom/.../mask.png --mask-b results/svs/.../mask.png

# three-panel difference figure
grandqc-overlay --mask-a A.png --mask-b B.png --out diff.png --label-a "IDC DICOM" --label-b "SVS"

# YBR_ICT prevalence for a collection (reads DICOM headers, no pixel download)
grandqc-inspect-headers --collection tcga_brca --transfer-syntax "JPEG 2000"
```

### Python API (the matched SVS-vs-DICOM flow)

```python
from grandqc_idc import (gdc_svs_by_barcode, gdc_download,
                         run_grandqc_dicom, run_grandqc_svs, compare)

SCRIPTS = "external/grandqc/01_WSI_inference_OPENSLIDE_QC"
bc = "TCGA-AC-A23G-01Z-00-DX1"

svs = gdc_download(gdc_svs_by_barcode(bc)["file_id"], f"data/gdc/{bc}.svs")   # original .svs
run_grandqc_dicom("data/idc", "results/dicom", SCRIPTS)   # DICOM -> wsidicom
run_grandqc_svs(svs, "results/svs", SCRIPTS)              # .svs  -> OpenSlide
print(compare(f"results/dicom/mask_qc/{bc}_mask.png",
              f"results/svs/mask_qc/{bc}.svs_mask.png"))   # format-equivalence
```

(IDC DICOM download uses `grandqc_idc.idc.download_dicom`, which needs the `idc` extra.)

---

## Notebooks

Each notebook states its purpose, inputs, expected outputs, environment, runtime, and GPU
need at the top, and exports results to CSV/JSON at the end. Every notebook opens with an
**Open in Colab** badge and self-bootstraps there (installs the `grandqc_idc` package and
deps, pins the GrandQC fork to the validated commit) — no local setup needed.

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
grandqc_idc/  installable package: codebook, metrics, readers, provenance, idc, overlays, cli
pyproject.toml  package metadata + console-script entry points
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
`.gitignore`. The package/notebooks download them on demand; `results/example_outputs/`
holds a few small masks and difference maps for illustration. All heavy artifacts are
pinned by checksum in `manifests/`.

## License & citation

Code under the [MIT License](LICENSE). If you use this work, see [CITATION.cff](CITATION.cff).
GrandQC, the model checkpoints, and the TCGA reference masks are the work of Weng/Tolkach
et al. and are cited there.
