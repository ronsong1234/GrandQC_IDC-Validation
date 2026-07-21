# Findings

All numbers below are measured; scripts and notebooks reproduce them. The 5-slide figures
come from the validated demo set; the header sweep covers all 1,104 TCGA-BRCA DX slides.

## 1. SVS–DICOM computational equivalence

Running the identical GrandQC pipeline (same fork commit, same published weights, MPP 1.5,
same 512 patches) on IDC DICOM vs the original GDC SVS. All values computed by
`grandqc_idc.metrics` (the canonical metric implementation); reproduced in
`results/summary_tables/five_slide_equivalence.csv`.

| Slide | Photometric | Whole-image | Within-shared-tissue | TW-Dice |
|-------|-------------|------------:|---------------------:|--------:|
| TCGA-A8-A0AB | RGB (J2K) | 99.9995 % | 100.0000 % | 1.0000 |
| TCGA-AC-A23C | YBR_ICT | 99.9290 % | 99.9706 % | 0.9995 |
| TCGA-AC-A23G | YBR_ICT | 99.9870 % | 99.9999 % | 0.9999 |
| TCGA-AC-A62V | YBR_ICT | 99.9123 % | 99.9678 % | 0.9992 |
| TCGA-MS-A51U | RGB | 99.9561 % | 100.0000 % | 0.9995 |
| **mean** | | **99.957 %** | **99.988 %** | **0.9996** |

No slide is *byte-identical* across formats (the closest, TCGA-A8-A0AB, is 99.9995 %);
byte-identity holds only for a rerun of the *same* input (determinism control below).

**Determinism control.** GrandQC rerun on the identical DICOM produces a byte-identical
mask (`np.array_equal == True`, 100.0000 %). So the ~0.04 % mean SVS–DICOM difference is a
real codec-level effect, not run-to-run noise.

**Decode floor.** Decoding the same level-0 region from the SVS and the DICOM differs by at
most **±1 grey level** everywhere — the two inputs reach GrandQC nearly pixel-identical.
Byte-identical output is therefore not achievable (the difference is in the codec, upstream
of the pipeline), and not necessary: equivalence is established to codec rounding.

## 2. The YBR_ICT decoding bug

IDC serves some TCGA slides as JPEG 2000 with `PhotometricInterpretation = YBR_ICT`.
OpenSlide 4.0.1 opens them without error but does not apply the inverse color transform,
so GrandQC's tissue detector sees a salmon-tinted image (mean RGB ≈ 210/133/133 instead of
H&E) and returns a **crisp but inverted** tissue mask. The cascade drops tissue-weighted
Dice from ~0.96 to ~0.49 on affected slides. `wsidicom` decodes YBR_ICT correctly; the
`idc-dicom-wsidicom` fork routes all DICOM through it.

**Prevalence (TCGA-BRCA DX H&E, n = 1,104):** 29 confirmed YBR_ICT (2.6 %; ≤34 / 3.1 %
counting 5 slides whose header re-read failed), across source sites AC (40×) and AO (20×).
Read directly from DICOM headers via S3 range requests — the value is not in the IDC index.
JPEG 2000 alone is *not* a proxy: 5 of the 39 J2K slides decode as RGB and are unaffected.

## 3. Zenodo reference-provenance gap

The published Zenodo TCGA masks are used in this project only as a *secondary* comparison,
because the public GrandQC release does not reproduce them.

- The authors' 2024 code (`cpath-ukk/grandqc` @ `84f3fec`, "VERSION: 1", 2024-11-09 — the
  same day as the Zenodo deposits) run on the original SVS gives **tissue IoU ≈ 0.70 vs
  Zenodo** on the large-rim slides — the same gap our fork produces.
- The 2024 code and our fork agree with **each other** at IoU **0.9865–0.9975** on all 5
  slides, and diverge from Zenodo by the same amount per slide. The gap is release-wide, not
  a fork artifact.
- Published weights are the 2024 weights (strict `load_state_dict`: 0 missing / 0 unexpected
  keys, 492 tensors). There is only one public tissue checkpoint, so a two-file tensor diff
  is impossible; the clean strict load is the strongest available proof.
- The public tissue detector is pure `np.argmax` with **no threshold, morphology, or
  connected-component step** — there is no stage in which Zenodo's tighter boundaries and
  internal holes could be produced. The reference procedure is not recoverable from the
  released materials.

Full audit and per-slide table: `provenance_experiment/PROVENANCE_AUDIT.md`.
