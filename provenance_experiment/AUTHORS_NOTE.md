# Draft note to the GrandQC authors

> **Status: DRAFT — not sent.** This is a reproducibility inquiry, not a bug report. The
> tone is collaborative: the goal is to learn which exact configuration produced the
> published masks. Review and edit before sending; confirm the channel (GitHub issue on
> `cpath-ukk/grandqc`, or email) with your mentor first.

---

**Subject:** Reproducing the Zenodo TCGA QC masks from the public GrandQC 2024 release

Dear GrandQC authors,

Thank you for releasing GrandQC, the model checkpoints, and the TCGA QC masks — they have
been very useful. While validating a DICOM-based QC pipeline against your published masks, I
found that I cannot reproduce the Zenodo tissue boundaries from the public 2024 code and
released weights, and I would be grateful for guidance on the exact reference-generation
configuration.

**What I did (fully reproducible):**

- Ran `cpath-ukk/grandqc` @ `84f3fec` ("VERSION: 1", 2024-11-09), unmodified except
  `DEVICE='cuda'→'cpu'`, on the original TCGA `.svs` files from GDC.
- Used the published checkpoints: `Tissue_Detection_MPP10.pth` (Zenodo 14507273) and
  `GrandQC_MPP15.pth` (Zenodo 14041538). The tissue checkpoint loads into the 2024
  `smp.UnetPlusPlus` architecture with `strict=True` (0 missing / 0 unexpected keys).

**What I found (5 TCGA-BRCA DX slides):**

| | tissue IoU |
|---|---|
| authors' 2024 code vs Zenodo masks | 0.70–0.98 (≈0.70 on high-disagreement slides) |
| my IDC-DICOM fork vs Zenodo masks | 0.70–0.98 (tracks the above within ≤0.007/slide) |
| authors' 2024 code vs my fork | **0.986–0.998** |

So two independent public runs agree closely with each other but both diverge from the
Zenodo masks in the same slide-specific regions — the published masks appear to have tighter
tissue boundaries and internal holes that the public code's `argmax` tissue detector (no
threshold / morphology / post-processing) does not produce.

**My question:** which exact code revision, tissue checkpoint, threshold/preprocessing, and
any post-processing (morphology, connected-component filtering, resolution) were used to
generate the Zenodo TCGA masks? If an internal or earlier pipeline was used, that would
fully explain the gap.

**Reproducibility package (attached / linked):**

- Slide ID(s), e.g. `TCGA-AC-A23G-01Z-00-DX1`; GDC file UUIDs + SVS SHA-256 (see
  `manifests/slide_manifest.csv`).
- Code commit `84f3fec`; the one-line device diff (`2024_code_device_patch.diff`).
- Model SHA-256s and strict-load result (`manifests/model_manifest.csv`,
  `PROVENANCE_AUDIT.md`).
- Difference overlays (`figures/five_panel_a23g.png`) and per-slide IoU
  (`prov_5slide_results.json`).
- A minimal rerun script (`minimal_rerun.py`).

Thank you very much for any pointers.

Best regards,
Ronak Singh
Georgetown University MS HIDS · Harvard Medical School (Fedorov Lab)

---

*If there is no response or the masks cannot be reproduced, this is documented transparently
as an unresolved provenance limitation in `docs/limitations.md` (item 2) — the validation's
primary reference is the matched fresh-SVS baseline, not the Zenodo masks, so the finding
does not block the equivalence result.*
