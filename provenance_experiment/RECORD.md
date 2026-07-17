# Provenance Experiment — Record

**Question.** Can the original `.svs` reproduce the Zenodo tissue boundary using the
GrandQC authors' own archived 2024 code and published weights? (If yes, the IDC fork
introduced the "rim"; if no, the discrepancy is a reference-provenance issue outside the
public release.)

**Answer. No.** The authors' 2024 code, with the authors' published weights, run on the
exact original `.svs`, produces essentially the same rim as the IDC pipeline. The rim is
**not** introduced by the fork or by the DICOM route.

---

## Method

- **Slide:** `TCGA-AC-A23G-01Z-00-DX1` (a high-disagreement / large-rim slide). Original
  Aperio `.svs` downloaded from GDC (file the Zenodo mask was computed from).
- **Code:** `cpath-ukk/grandqc` commit `84f3fec` ("VERSION: 1", 2024-11-09 — same day as
  the Zenodo mask and model deposits). This is the authors' released code; **no Zenodo
  software archive exists** (records 14041578 / 14041538 / 14507273 contain only masks and
  `.pth` checkpoints). See `2024_code_commit.txt`.
- **Only modification:** `DEVICE = 'cuda'` → `'cpu'` in `wsi_tis_detect.py` and `main.py`
  (no accelerator available). Tissue-detection logic untouched. Full diff in
  `2024_code_device_patch.diff`.
- **Weights:** the published Zenodo checkpoints, confirmed identical to the 2024 internal
  files by clean state-dict load:
  - `Tissue_Detection_MPP10.pth` (Zenodo 14507273) = 2024 `Vs04_model_E10_dict.pth`
  - `GrandQC_MPP15.pth` (Zenodo 14041538) = 2024 `v35_E14.pth`
- **Comparison:** tissue support (tissue vs background) of each run against the Zenodo
  reference mask, at reference resolution (nearest-neighbor upscale of the MPP-10 tissue
  mask). The 2024 output is 512×512 (padded — the 2024 code lacks the small-thumbnail crop
  the fork adds), so it was cropped bottom-right to the thumbnail size before comparison,
  identically to the fork.

## Results (`comparison_results.csv`, `comparison_figure.png`)

| Comparison | Tissue IoU | Rim (tissue in run, background in other) |
|---|---:|---:|
| **Authors' 2024 code vs Zenodo** | **0.7008** | 1,293,821 px |
| IDC fork vs Zenodo | 0.6986 | 1,307,163 px |
| **Authors' 2024 code vs IDC fork** | **0.9955** | — |

The two public runs agree with **each other** at IoU 0.9955 but both sit at ~0.70 against
Zenodo. Whatever produced the published masks differs from both public runs by the same
margin.

## Conclusion

1. The rim is inherent to the **public GrandQC release** (code + weights), not to the IDC
   DICOM conversion and not to the `fedorov/grandqc` fork.
2. The tissue checkpoint and artifact checkpoint are the published ones (verified), so the
   difference is not the weights.
3. The remaining provenance — whatever internal pipeline/post-processing yielded the
   tighter Zenodo boundary — is **absent from the public release**. The legitimate next
   step is to contact the GrandQC authors with: slide ID `TCGA-AC-A23G-01Z-00-DX1`, code
   commit `84f3fec`, these measured results, and the difference image.

### Incidental findings
- The 2024 code has a **small-slide bug**: when the MPP-10 thumbnail is smaller than one
  512 patch, it emits a 512×512 padded mask and never crops back (the fork fixes this with
  `end_image[-height:, -width:]`).
- The 2024 `main.py` `torch.load` predates PyTorch 2.6's `weights_only=True` default, so
  the artifact stage needs `weights_only=False` to run on modern PyTorch. (The tissue
  stage — which determines the rim — completed normally.)

## Files in this folder

| File | Contents |
|------|----------|
| `masks_2024_authors_code/…_MASK.png` | 2024-code tissue mask (raw 512×512) |
| `masks_2024_authors_code/…_MASK_COL.png` | 2024-code color tissue overlay |
| `masks_2024_authors_code/…svs.jpg` | tissue-detector input thumbnail |
| `masks_2024_authors_code/…_ZENODO_reference.png` | Zenodo reference mask (for comparison) |
| `masks_2024_authors_code/…_FORK_tis_det.png` | IDC-fork tissue mask (for comparison) |
| `comparison_results.csv` | the IoU / rim table above |
| `comparison_figure.png` | 4-panel: 2024 \| fork \| Zenodo \| 2024-vs-Zenodo diff |
| `2024_code_commit.txt` | exact commit hash run |
| `2024_code_device_patch.diff` | the device-only modification |
