"""Shared utilities: mask I/O, the GrandQC codebook, and comparison metrics.

The metric conventions here are the single source of truth for the whole repo and
are covered by tests/test_metrics.py. See CODEBOOK.md for the encoding definitions.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# --- GrandQC artifact mask codebook (1-based; 0 = unwritten margin, not a class) ---
CLASS_NAMES = {
    0: "Margin (unwritten)",
    1: "Clean tissue",
    2: "Folds",
    3: "Dark spots",
    4: "Pen marks",
    5: "Bubbles/edges",
    6: "Out-of-focus",
    7: "Background",
}
PALETTE = {
    1: (128, 128, 128), 2: (255, 99, 71), 3: (0, 255, 0), 4: (255, 0, 0),
    5: (255, 0, 255), 6: (75, 0, 130), 7: (255, 255, 255),
}
BACK_CLASS = 7
MARGIN = 0
TISSUE_CLASSES = (1, 2, 3, 4, 5, 6)


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_mask(path: str | Path) -> np.ndarray:
    return np.array(Image.open(path))


def tissue_mask(mask: np.ndarray) -> np.ndarray:
    """Boolean tissue support: any class 1-6. Excludes background (7) and margin (0)."""
    return np.isin(mask, TISSUE_CLASSES)


def colorize(mask: np.ndarray) -> np.ndarray:
    out = np.full(mask.shape + (3,), 255, np.uint8)
    for v, rgb in PALETTE.items():
        out[mask == v] = rgb
    out[mask == MARGIN] = 255
    return out


class MaskShapeMismatch(ValueError):
    """Two masks that should align have different shapes."""


def _align(a: np.ndarray, b: np.ndarray, allow_crop: bool = False):
    """Return the two masks at a common shape.

    By default a shape mismatch RAISES — for the primary SVS-DICOM comparison, differing
    dimensions signal a real alignment/dimension error and must not be silently hidden.
    Pass ``allow_crop=True`` (the provenance experiment's historical-padding case) to crop
    both to the minimum common shape; the crop amount is reported via a warning.
    """
    if a.shape == b.shape:
        return a, b
    if not allow_crop:
        raise MaskShapeMismatch(
            f"mask shapes differ: {a.shape} vs {b.shape}. Matched SVS-DICOM masks must "
            f"share dimensions; pass allow_crop=True only for the known padding case."
        )
    h, w = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
    import warnings
    warnings.warn(
        f"cropping to common shape ({h}, {w}): dropped rows a={a.shape[0]-h}/b={b.shape[0]-h}, "
        f"cols a={a.shape[1]-w}/b={b.shape[1]-w} (originals {a.shape}, {b.shape})",
        stacklevel=2,
    )
    return a[:h, :w], b[:h, :w]


def agreement(a: np.ndarray, b: np.ndarray, allow_crop: bool = False) -> dict:
    """Whole-image and within-shared-tissue label agreement (%), margin excluded."""
    a, b = _align(a, b, allow_crop)
    valid = (a != MARGIN) & (b != MARGIN)
    both_tissue = tissue_mask(a) & tissue_mask(b)
    whole = (a[valid] == b[valid]).mean() * 100 if valid.any() else float("nan")
    within = (a[both_tissue] == b[both_tissue]).mean() * 100 if both_tissue.any() else float("nan")
    return {"whole_image": whole, "within_shared_tissue": within}


def tissue_iou(a: np.ndarray, b: np.ndarray, allow_crop: bool = False) -> float:
    a, b = _align(a, b, allow_crop)
    ta, tb = tissue_mask(a), tissue_mask(b)
    union = (ta | tb).sum()
    return float((ta & tb).sum() / union) if union else 1.0


def dice(a_bool: np.ndarray, b_bool: np.ndarray) -> float | None:
    tot = a_bool.sum() + b_bool.sum()
    return float(2.0 * np.logical_and(a_bool, b_bool).sum() / tot) if tot else None


def tw_dice(ref: np.ndarray, pred: np.ndarray, allow_crop: bool = False) -> float:
    """Tissue-weighted Dice: tissue (1-6) vs background (7), margin excluded."""
    ref, pred = _align(ref, pred, allow_crop)
    valid = (ref != MARGIN) & (pred != MARGIN)
    return dice(tissue_mask(ref)[valid], tissue_mask(pred)[valid])


def macro_dice(ref: np.ndarray, pred: np.ndarray, absent_as_zero: bool = True,
               allow_crop: bool = False) -> float:
    """Unweighted mean Dice over the 7 classes. `absent_as_zero` toggles the two
    conventions that differ by ~0.25 on small sets (see CODEBOOK.md)."""
    ref, pred = _align(ref, pred, allow_crop)
    valid = (ref != MARGIN) & (pred != MARGIN)
    r, p = ref[valid], pred[valid]
    scores = []
    for c in range(1, 8):
        d = dice(r == c, p == c)
        if d is None:
            if absent_as_zero:
                scores.append(0.0)
        else:
            scores.append(d)
    return float(np.mean(scores)) if scores else float("nan")
