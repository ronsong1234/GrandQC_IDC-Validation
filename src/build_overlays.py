"""Build a three-panel comparison figure (mask A | mask B | difference) for two masks.

    python src/build_overlays.py --mask-a A.png --mask-b B.png --out fig.png \
        --label-a "IDC DICOM" --label-b "Original SVS"

Difference panel: red = tissue only in A, blue = tissue only in B, amber = class clash in
shared tissue, grey = agree. Cropped to the tissue.
"""
import argparse

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from utils import MaskShapeMismatch, colorize, load_mask, tissue_iou, tissue_mask


def figure(path_a, path_b, out, label_a, label_b, allow_crop=False):
    a, b = load_mask(path_a), load_mask(path_b)
    if a.shape != b.shape:
        if not allow_crop:
            raise MaskShapeMismatch(
                f"mask shapes differ: {a.shape} vs {b.shape}. Pass --allow-common-crop "
                f"only for the known padding case."
            )
        h, w = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
        print(f"  cropping to common ({h}, {w}): dropped a={a.shape}->{h,w}, b={b.shape}->{h,w}")
        a, b = a[:h, :w], b[:h, :w]
    ta, tb = tissue_mask(a), tissue_mask(b)
    ys, xs = np.where(ta | tb)
    if len(ys):
        pad = 40
        sl = (slice(max(0, ys.min() - pad), ys.max() + pad),
              slice(max(0, xs.min() - pad), xs.max() + pad))
    else:
        sl = (slice(0, h), slice(0, w))

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
    print(f"wrote {out}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mask-a", required=True)
    p.add_argument("--mask-b", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--label-a", default="A")
    p.add_argument("--label-b", default="B")
    p.add_argument("--allow-common-crop", action="store_true",
                   help="crop to the common shape instead of erroring on a size mismatch")
    args = p.parse_args()
    figure(args.mask_a, args.mask_b, args.out, args.label_a, args.label_b,
           allow_crop=args.allow_common_crop)


if __name__ == "__main__":
    main()
