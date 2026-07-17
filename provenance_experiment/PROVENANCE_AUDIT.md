# Provenance Audit — full traceability record

Companion to `RECORD.md`. This file makes the provenance finding auditable end-to-end and
records the multi-slide confirmation. Everything below is measured, not asserted.

---

## 1. Multi-slide confirmation (was it just A23G?)

The authors' 2024 code (`84f3fec`), the IDC fork, and the Zenodo reference, compared on
**tissue support** (tissue vs background) after identical margin-exclusion and bottom-right
crop handling. Tissue IoU:

| Slide | Rim class | 2024 vs Zenodo | Fork vs Zenodo | **2024 vs Fork** |
|-------|-----------|---------------:|---------------:|-----------------:|
| TCGA-AC-A23G | large | 0.7008 | 0.6986 | **0.9955** |
| TCGA-AC-A23C | large | 0.8085 | 0.8073 | **0.9942** |
| TCGA-AC-A62V | large | 0.8504 | 0.8435 | **0.9865** |
| TCGA-A8-A0AB | near-exact | 0.9717 | 0.9703 | **0.9966** |
| TCGA-MS-A51U | near-exact | 0.9802 | 0.9788 | **0.9975** |
| **mean** | | **0.8623** | **0.8597** | **0.9941** |

**Pattern (systematic, not isolated):** the two public implementations agree with *each
other* at 0.986–0.998 on every slide, and diverge from Zenodo by the *same* amount per
slide (2024-vs-Zenodo tracks fork-vs-Zenodo within 0.001–0.007 everywhere). The divergence
is a property of the public release, and it is slide-specific in the same way for both
implementations. Data: `prov_5slide_results.json`; masks: `masks_2024_authors_code_5slide/`.

---

## 2. Auditable manifest

### Code
- **GrandQC authors' code:** `github.com/cpath-ukk/grandqc` commit `84f3fec`
  ("GrandQC: VERSION: 1", 2024-11-09 — same day as the Zenodo deposits). Only modification:
  `DEVICE='cuda'`→`'cpu'` (see `2024_code_device_patch.diff`). No Zenodo software archive
  exists.
- **IDC fork:** `github.com/fedorov/grandqc` branch `idc-dicom-wsidicom`.

### Model checkpoints (SHA-256)
| File | Zenodo record | SHA-256 |
|------|--------------|---------|
| `Tissue_Detection_MPP10.pth` | 14507273 | `0e3577628a553774419a5b87a2947531988e07175b9e1a8048f53b6188f4d76e` |
| `GrandQC_MPP15.pth` | 14041538 | `6e90ec8548d4050734c30e30d5ca7fe67e84b59b1dd8ae338447dad90bae4ff1` |

### Source slides (GDC, open access)
| Barcode | GDC file_id | SHA-256 (SVS) | Bytes |
|---------|-------------|---------------|-------|
| TCGA-AC-A23G | `2449ff02-6925-4f25-9074-7c5fbeab0bd2` | `3a4455515ba916bb…7ccee49` | 41,783,236 |
| TCGA-AC-A23C | `d2d43332-6848-4e05-908a-9b8095d4aedf` | `7c3b337aa0a026e0…f5422a12` | 55,177,906 |
| TCGA-AC-A62V | `2b5c424a-e8d9-4412-b612-e3adcf98dffd` | `9c4387e3d4ff1b04…00388131` | 57,528,662 |
| TCGA-A8-A0AB | `763a8540-c78d-4718-96ff-d2c926cf5390` | `181168e4744b5398…06aa4851` | 149,503,036 |
| TCGA-MS-A51U | `910b5349-046d-483e-8277-fcaa07cb35ca` | `78f04cfd183f1cbd…7c0d2aad` | 71,458,533 |

### Environment
```
python 3.13.14 | torch 2.12.1+cpu | segmentation-models-pytorch 0.3.1
numpy 2.4.2 | pillow 12.2.0 | opencv 4.13.0
openslide-python 1.4.6 | libopenslide 4.0.1
device: cpu (deterministic — verified byte-identical on rerun, array_equal=True)
```

### Checkpoint ↔ architecture verification
A **tensor-by-tensor diff between the internal 2024 checkpoint and the published one is
not possible**: the internal name `Vs04_model_E10_dict.pth` was never released — only
`Tissue_Detection_MPP10.pth` exists publicly. The strongest available proof is a **strict
state-dict load** of the published checkpoint into the 2024 architecture:

```
smp.UnetPlusPlus(encoder_name='timm-efficientnet-b0', classes=2, activation=None)
load_state_dict(strict=True) -> missing_keys=0, unexpected_keys=0
492 tensors, 6,614,533 parameters
```

Zero key mismatch under `strict=True` means the published checkpoint *is* the exact 2024
tissue architecture's weights. (When the file was copied to the 2024 name for the run, both
had SHA `0e3577…` — same bytes, by construction.)

---

## 3. Why no "historical configuration" search was run

The plan proposed tuning tissue threshold, connected-component filtering, and morphology on
the SVS route. **These knobs do not exist in the public tissue-detection code.** Source
inspection of `wsi_tis_detect.py` @ `84f3fec`:

| Candidate knob | Present in public code? |
|----------------|-------------------------|
| probability threshold | **absent** — decision is `np.argmax` over 2 channels |
| morphology (erode/dilate/open/close) | **absent** |
| connected-component / small-object removal | **absent** |
| thumbnail interpolation override | absent (uses OpenSlide `get_thumbnail` default) |

The public tissue detector is **argmax with no post-processing**. It therefore cannot, by
any parameter choice, produce Zenodo's tighter boundaries and internal tissue holes —
there is no stage in which such shaping could occur. This is stronger than a failed
parameter sweep: the search space in the released code is essentially empty, so the
reference-generation procedure is **not recoverable from the released materials**. Any
reproduction would require code the authors did not release (a different tissue model
version, or a post-processing stage).

---

## 4. Conclusion

1. The rim/divergence from Zenodo is **release-wide and systematic** — reproduced by the
   authors' own 2024 code on 5 slides, tracking the fork within ≤0.007 IoU per slide.
2. Weights and architecture are the published ones (verified by SHA + strict load).
3. The public code has no post-processing capable of producing the Zenodo boundaries, so
   the reference procedure cannot be recovered from released materials.
4. **Next step:** contact the GrandQC authors (see `AUTHORS_NOTE.md` when drafted) with
   this manifest and ask which exact code revision, checkpoint, and post-processing
   generated the Zenodo masks. A no-response or non-reproduction is itself documented here
   as an unresolved, transparently-recorded limitation.
