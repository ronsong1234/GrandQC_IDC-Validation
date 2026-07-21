# Methods

## Design: hold the pipeline fixed, vary the input format

The research question is whether replacing SVS with IDC DICOM changes GrandQC output. The
comparison therefore varies **only** the input format and holds everything else constant:
the fork commit, both model checkpoints, MPP (10 for tissue, 1.5 for artifact), patch size
(512), and the metric code (`grandqc_idc.metrics`).

```
IDC DICOM ──wsidicom──┐
                      ├── GrandQC (same code+weights) ── matched mask comparison   [PRIMARY]
GDC SVS ──OpenSlide───┘
                      └── Zenodo reference ── provenance analysis                   [SECONDARY]
```

## Why the SVS baseline, and why from GDC

A claim about IDC needs a reference from *outside* IDC, or it is circular. The original
Aperio `.svs` files live in the **GDC** (Genomic Data Commons) — an independent archive, and
the exact files the Zenodo masks were computed from. The Zenodo mask filename embeds the
source `.svs` filename, so each barcode resolves to its GDC file (`grandqc_idc.gdc_svs_by_barcode`).
Transcoding the DICOM into SVS would defeat the test — the pixels would still be the DICOM's.

## Reader routing (the crux)

GrandQC's `open_slide()` dispatches on input type: a DICOM series directory goes to
`wsidicom`, a single-file WSI (`.svs`) falls back to OpenSlide. This is not optional — an
earlier "OpenSlide-first, wsidicom-on-exception" arrangement never triggered the fallback,
because OpenSlide opens YBR_ICT DICOM *without raising* and silently mis-decodes it
(Finding 2). `tests/test_reader_routing.py` pins the contract.

## Metrics

Defined once in `grandqc_idc.metrics`, tested in `tests/test_metrics.py`:

- **Whole-image agreement** — % equal label over the common non-margin area.
- **Within-shared-tissue agreement** — % equal label where both masks call tissue (1–6);
  isolates the artifact model from the tissue-detection boundary.
- **Tissue IoU** — intersection-over-union of tissue support.
- **Tissue-weighted Dice** — tissue (1–6) vs background (7).
- **Macro Dice** — mean over 7 classes; convention (absent-as-0 vs present-only) reported
  explicitly because it moves the value by ~0.25 on small sets.

The unwritten floor-grid margin (value 0) is excluded from every metric.

## Determinism

GrandQC is deterministic on CPU (verified byte-identical rerun). All validated numbers were
produced on CPU with the pinned environment in `manifests/environment_manifest.txt`, so the
comparison has no run-to-run noise to confound the tiny format effect.

## Stratified cohort

The 22-slide validation cohort (`config/stratified_22_slide_cohort.csv`) oversamples the
rare-but-critical strata (YBR_ICT, Zeiss scanner) rather than taking the smallest slides.
Codec, source-site and magnification are confounded in TCGA-BRCA (see `docs/limitations.md`),
so the cohort demonstrates equivalence *across* strata rather than attributing cause to any
one axis.

## Provenance reconstruction

`04_reference_provenance.ipynb` / `provenance_experiment/` run the authors' 2024 code
(`84f3fec`, device-patched to CPU only) with the published weights on the original SVS, and
compare tissue support against Zenodo after identical margin-exclusion and crop handling.
See `provenance_experiment/PROVENANCE_AUDIT.md` for the full manifest.
