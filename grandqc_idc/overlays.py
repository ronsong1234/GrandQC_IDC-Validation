"""Difference-overlay figures (requires the optional `matplotlib` dependency)."""
from __future__ import annotations

import numpy as np

from .metrics import MaskShapeMismatch, colorize, load_mask, tissue_iou, tissue_mask


def difference_figure(path_a, path_b, out, label_a="A", label_b="B", allow_crop=False):
    """Three-panel figure: mask A | mask B | difference. Raises on shape mismatch unless
    allow_crop (reports the crop). Difference: red = tissue only in A, blue = only in B,
    amber = class clash in shared tissue, grey = agree."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    a, b = load_mask(path_a), load_mask(path_b)
    if a.shape != b.shape:
        if not allow_crop:
            raise MaskShapeMismatch(
                f"mask shapes differ: {a.shape} vs {b.shape}. Pass allow_crop=True only for "
                f"the known padding case.")
        h, w = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
        print(f"  cropping to common ({h}, {w}) from {a.shape}, {b.shape}")
        a, b = a[:h, :w], b[:h, :w]

    ta, tb = tissue_mask(a), tissue_mask(b)
    ys, xs = np.where(ta | tb)
    pad = 40
    sl = ((slice(max(0, ys.min() - pad), ys.max() + pad),
           slice(max(0, xs.min() - pad), xs.max() + pad)) if len(ys)
          else (slice(0, a.shape[0]), slice(0, a.shape[1])))

    diff = np.full((sl[0].stop - sl[0].start, sl[1].stop - sl[1].start, 3), 255, np.uint8)
    both = ta & tb
    diff[both[sl]] = (230, 230, 230)
    diff[(ta & ~tb)[sl]] = (255, 0, 0)
    diff[(tb & ~ta)[sl]] = (0, 90, 255)
    diff[(both & (a != b))[sl]] = (255, 190, 0)

    fig, ax = plt.subplots(1, 3, figsize=(13, 4.5))
    ax[0].imshow(colorize(a[sl])); ax[0].set_title(label_a)
    ax[1].imshow(colorize(b[sl])); ax[1].set_title(label_b)
    ax[2].imshow(diff); ax[2].set_title(f"Difference (tissue IoU {tissue_iou(a, b):.4f})")
    for x in ax:
        x.set_xticks([]); x.set_yticks([])
    fig.tight_layout()
    fig.savefig(out, dpi=120, facecolor="white")
    plt.close(fig)
    return out
