# Dashboard integration

How this validation framework connects to the interactive QC dashboards
(`Grand_IDC` batch runner and `Grand_IDC_Live` FastAPI app).

## The one hard requirement the dashboards must honor

**DICOM series must be read through `wsidicom`, never OpenSlide.** This is the single
safety-critical result of the validation (Finding 2): OpenSlide silently mis-decodes
YBR_ICT JPEG 2000 slides and inverts the tissue mask, with no error raised. Any dashboard
that ingests IDC DICOM must use the `DicomSlide`/`wsidicom` reader path.

- The `Grand_IDC_Live` `DicomSlide` shim already uses `wsidicom` directly, so it is not
  exposed to the bug. `tests/test_reader_routing.py` in this repo encodes the contract; wire
  an equivalent assertion into the dashboard's CI so a future refactor cannot regress it.

## What the dashboard can reuse from here

- **`grandqc_idc` (the package)** — the mask codebook and metric functions (single source of truth). The
  dashboard's per-slide QC summary should compute tissue % and per-class % from the same
  `TISSUE_CLASSES` / `BACK_CLASS` / margin conventions, so numbers match across tools.
- **`grandqc-compare` / `grandqc_idc.compare`** — if the dashboard ever offers an SVS-vs-DICOM check for a user
  slide, this is the drop-in comparison.
- **`manifests/`** — pin the same model SHA-256s so the dashboard provably runs the
  validated weights.

## What to surface to dashboard users

- A per-slide **codec/photometric badge** (`grandqc_idc.photometric_for_series`): flag
  YBR_ICT slides so users know they *require* the wsidicom path.
- The **matched-baseline framing**: if the dashboard shows agreement against any reference,
  label it "computational equivalence to GrandQC," not "accuracy" (see
  `docs/limitations.md`).

## What NOT to carry over

- Do not use the Zenodo masks as a live correctness reference in the dashboard — they are not
  reproducible from public materials (Finding 3). They are for the provenance study only.
