# Codebook — GrandQC × IDC DICOM QC Pipeline

Authoritative reference for every coded value used across this project (mask pixel
values, DICOM metadata codes, cohort strata, and comparison metrics). Each entry cites
where the code is *defined*, so nothing here rests on assumption.

> **Provenance of this file.** Class labels and colors are transcribed from the GrandQC
> source (`01_WSI_inference_OPENSLIDE_QC/wsi_process.py` and `wsi_colors.py`, commit
> `84f3fec`, "VERSION: 1", 2024-11-09). DICOM codes are read from the slide headers and
> the DICOM standard. Cohort figures are measured from IDC `v24` and Zenodo record
> 14041578. Metrics are as computed in the notebooks.

---

## 1. Artifact-segmentation mask (`mask_qc/<barcode>_mask.png`)

Single-channel 8-bit PNG. One integer class per pixel. **Values are 1-based** — this is
the single most error-prone point in the whole pipeline, so it is stated first.

| Value | Class (`CLASS_MAPPING`) | Short name | Overlay color (R,G,B) | Meaning |
|------:|-------------------------|-----------|-----------------------|---------|
| **0** | *(none)* | Margin | — (rendered white) | **Not a class.** Unwritten right/bottom remainder left by the floor-tiling grid. Exclude from every metric. |
| **1** | Normal Tissue | Clean tissue | 128,128,128 (grey) | Tissue with no detected artifact |
| **2** | Fold | Folds | 255,99,71 (tomato) | Tissue folded during mounting |
| **3** | Darkspot & Foreign Object | Dark spots | 0,255,0 (green) | Debris / opaque contamination |
| **4** | PenMarking | Pen marks | 255,0,0 (red) | Ink annotation on the glass |
| **5** | Edge & Air Bubble | Bubbles/edges | 255,0,255 (magenta) | Trapped air or slide-edge optical distortion |
| **6** | OOF | Out-of-focus | 75,0,130 (indigo) | Scanner autofocus failure / blur |
| **7** | Background | Background | 255,255,255 (white) | Non-tissue (glass) |

- **Source:** `wsi_process.py` `CLASS_MAPPING` (labels) and `wsi_colors.py` `colors_QC7`
  (colors). Color for value *v* is `colors_QC7[v-1]`.
- **`BACK_CLASS = 7`** is defined in `main.py`.
- **Tissue** = values 1–6. **Non-tissue** = value 7. **Margin** = value 0 (drop it).

---

## 2. Tissue-detection mask (`tis_det_mask/<barcode>_MASK.png`)

Separate, *binary* mask from Stage 1 (the MPP-10 tissue detector). **Do not confuse its
encoding with the artifact mask above — the polarity is inverted.**

| Value | Meaning |
|------:|---------|
| **0** | Tissue (patch is processed by the artifact model) |
| **1** | Background (patch forced to `BACK_CLASS = 7`) |

- **Source:** `wsi_process.py` — gate `np.count_nonzero(td_patch == 0) > 50` selects
  tissue; `np.where(td_patch_ == 1, BACK_CLASS, mask_raw)` forces background.

---

## 3. DICOM PhotometricInterpretation (tag 0028,0004)

The pixel color encoding. **This is the axis behind the OpenSlide color bug** and is *not*
stored in the IDC index — it must be read from the slide header.

| Code | Meaning | Behavior in this project |
|------|---------|--------------------------|
| `RGB` | Direct RGB samples | Decodes correctly under any reader |
| `YBR_ICT` | Luma/chroma, JPEG 2000 irreversible color transform | **OpenSlide 4.0.1 fails to apply the inverse transform** → salmon image → inverted tissue mask. Must be read via wsidicom. |

- **Prevalence (TCGA-BRCA DX H&E, n=1,104):** 29 confirmed `YBR_ICT` (2.6%; ≤34 / 3.1%
  counting 5 unresolved), across source sites AC (40×) and AO (20×). Measured by HTTP
  range-reading the 39 JPEG-2000 slide headers.

---

## 4. DICOM TransferSyntaxUID (codec) — IDC index column `transfer_syntax_name`

| UID | Name | TCGA-BRCA DX count |
|-----|------|-------------------:|
| `1.2.840.10008.1.2.4.50` | JPEG Baseline (Process 1) | 1,065 |
| `1.2.840.10008.1.2.4.91` | JPEG 2000 Image Compression | 39 |

- **Note:** JPEG 2000 is a *superset* of the vulnerable slides. Of the 39 J2K slides, 29
  are `YBR_ICT` (vulnerable) and 5 decode as `RGB` (safe); 5 unresolved. Codec alone does
  not predict the bug — photometric interpretation does.

---

## 5. Scanner / Manufacturer — IDC index columns `Manufacturer`, `ManufacturerModelName`

| Manufacturer | Model (as recorded) | TCGA-BRCA DX count |
|--------------|--------------------|-------------------:|
| Leica Biosystems | Aperio converted by com.pixelmed.convert.TIFFToDicom | 1,014 |
| Carl Zeiss | Mirax converted by com.pixelmed.convert.TIFFToDicom | 90 |

---

## 6. Magnification / resolution

| Objective | Base MPP (µm/px) | `min_PixelSpacing_2sf` (mm) | TCGA-BRCA DX count |
|-----------|------------------|-----------------------------|-------------------:|
| 40× | ≈ 0.25 | ≤ 0.0004 | 1,053 |
| 20× | ≈ 0.50 | ≥ 0.0004 | 51 |

- **Model resolutions:** tissue detection runs at **MPP 10** (≈1×); artifact segmentation
  at **MPP 1.5** (≈7×, the recommended default), 512×512 patches.
- **Confound (documented):** in TCGA-BRCA, magnification, source-site, and codec travel
  together (20× ≈ site AO; `YBR_ICT` ≈ sites AC/AO; Zeiss ≈ JPEG Baseline). A fully
  orthogonal stratification is not achievable from this collection.

---

## 7. TCGA barcode structure

`TCGA-<SS>-<PPPP>-<sample><vial>-<portion><analyte>-<plate><center>`, e.g.
`TCGA-AC-A23G-01Z-00-DX1`.

| Field | Example | Meaning |
|-------|---------|---------|
| `<SS>` | `AC` | **Tissue source site** (institution). Used as the "institution" stratum. |
| `<PPPP>` | `A23G` | Participant |
| sample | `01` | 01 = primary solid tumor |
| `DX1` | `DX1` | **Diagnostic** slide (FFPE, H&E). `DX` = diagnostic; `TS`/`BS` = frozen. |

---

## 8. Comparison metrics (as used in Part 6 and the SVS study)

| Metric | Definition | Notes |
|--------|-----------|-------|
| **Whole-image agreement** | % of pixels with equal label, over the common (non-margin) area | Background-dominated; flatters mostly-glass slides |
| **Within-shared-tissue agreement** | % equal label, restricted to pixels both masks call tissue (1–6) | Isolates the artifact model from the tissue-detection boundary |
| **Rim** | pixels tissue in run A, background (7) in run B | The one-sided tissue-detection boundary difference |
| **Clash** | pixels both call tissue but assign different classes | Genuine artifact-class disagreement |
| **TW-Dice** (tissue-weighted) | Dice of tissue (1–6) vs background (7) | Comparable to GrandQC paper's 0.957; project value **0.9605** |
| **Macro Dice** | unweighted mean Dice over the 7 classes | **Convention-dependent:** absent-in-both as 0 → 0.65; present-only → 0.90. State which. |
| **IoU (tissue)** | intersection-over-union of the tissue region | Used for tissue-support comparisons |

---

## 9. Models & data records

| Artifact | Source | Notes |
|----------|--------|-------|
| Tissue model | `Tissue_Detection_MPP10.pth` — Zenodo **14507273** | = 2024 internal `Vs04_model_E10_dict.pth`; state-dict for `smp.UnetPlusPlus` (timm-efficientnet-b0). Confirmed identical (clean load). |
| Artifact model | `GrandQC_MPP15.pth` — Zenodo **14041538** | = 2024 internal `v35_E14.pth`; full pickled model, MPP 1.5. |
| Reference masks | `BRCA.tar` — Zenodo **14041578** | 1,105 masks; 1,104 overlap IDC BRCA-DX. **No code archive in this record.** |
| Authors' code | GitHub `cpath-ukk/grandqc` `84f3fec` | "VERSION: 1", 2024-11-09 (same day as masks). No Zenodo software DOI exists. |
| IDC fork | `fedorov/grandqc` `idc-dicom-wsidicom` | Adds wsidicom reader (fixes YBR_ICT), device auto-select, small-slide crop. Tissue path functionally identical to upstream (IoU 0.9955). |

---

## 10. Key result codes (for cross-reference in the report)

| Finding | Value |
|---------|-------|
| YBR_ICT decode bug, pre-fix TW-Dice | 0.49 (three affected slides 0.03–0.32) |
| Post-fix TW-Dice (5-slide) | 0.96 |
| DICOM vs SVS, same pipeline | 99.960% whole-image · 99.988% within-tissue · ΔTW-Dice 0.0002 |
| Raw decode floor (SVS vs DICOM, level 0) | max ±1 grey level |
| Authors' 2024 code vs Zenodo (tissue IoU) | 0.70 — **does not reproduce the reference** |
| 2024 code vs IDC fork (tissue IoU) | 0.9955 — fork did not introduce the rim |
