"""Minimal, self-contained reproduction of the provenance finding.

Reruns the tissue-support comparison between the authors' 2024 GrandQC code, the IDC fork,
and the Zenodo reference for one slide, and prints the tissue IoU table. Point it at three
mask PNGs you have already generated (see PROVENANCE_AUDIT.md for how each was produced).

    python minimal_rerun.py \
        --authors-2024 masks_2024_authors_code/TCGA-AC-A23G-01Z-00-DX1.svs_MASK.png \
        --fork  <fork tis_det_mask>.png \
        --zenodo <barcode>.<uuid>.svs_mask.png

The point of the finding: authors-2024 and fork agree with each other (~0.99), while BOTH
diverge from Zenodo (~0.70 on rim slides) — so the divergence is release-wide, not a fork
artifact.
"""
import argparse

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def up(m, shape):
    return np.array(Image.fromarray(m).resize(shape[::-1], Image.Resampling.NEAREST))


def iou(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 1.0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--authors-2024", required=True, help="2024-code tissue mask (0=tissue)")
    p.add_argument("--fork", required=True, help="fork tissue mask (0=tissue)")
    p.add_argument("--zenodo", required=True, help="Zenodo artifact mask (tissue = !=7 & !=0)")
    args = p.parse_args()

    zen = np.array(Image.open(args.zenodo))
    zt = (zen != 7) & (zen != 0)
    fork = np.array(Image.open(args.fork))
    m24 = np.array(Image.open(args.authors_2024))

    # 2024 code lacks the small-thumbnail crop; crop bottom-right to the fork's shape.
    th, tw = fork.shape
    m24c = m24[-th:, -tw:] if m24.shape != fork.shape else m24

    t24 = up(m24c, zen.shape) == 0
    tf = up(fork, zen.shape) == 0

    print(f"  authors-2024 vs Zenodo : tissue IoU {iou(t24, zt):.4f}")
    print(f"  fork         vs Zenodo : tissue IoU {iou(tf, zt):.4f}")
    print(f"  authors-2024 vs fork   : tissue IoU {iou(t24, tf):.4f}")
    print("\n  Expected pattern: the two public runs agree with each other (~0.99) while")
    print("  both diverge from Zenodo -> the reference is not reproducible from public code.")


if __name__ == "__main__":
    main()
