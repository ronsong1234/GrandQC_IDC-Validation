"""Compare two GrandQC masks and print/emit agreement, tissue IoU, and Dice.

    python src/compare_masks.py --mask-a A.png --mask-b B.png [--json out.json]
"""
import argparse
import json

from utils import agreement, load_mask, macro_dice, tissue_iou, tw_dice


def compare(path_a: str, path_b: str, allow_crop: bool = False) -> dict:
    a, b = load_mask(path_a), load_mask(path_b)
    # Report shapes always; a mismatch raises MaskShapeMismatch unless allow_crop is set.
    ag = agreement(a, b, allow_crop=allow_crop)
    return {
        "mask_a": path_a,
        "mask_b": path_b,
        "shape_a": list(a.shape),
        "shape_b": list(b.shape),
        "shapes_match": a.shape == b.shape,
        "whole_image_pct": round(ag["whole_image"], 4),
        "within_shared_tissue_pct": round(ag["within_shared_tissue"], 4),
        "tissue_iou": round(tissue_iou(a, b, allow_crop=allow_crop), 4),
        "tw_dice": round(tw_dice(a, b, allow_crop=allow_crop), 4),
        "macro_dice_absent_as_zero": round(macro_dice(a, b, True, allow_crop=allow_crop), 4),
        "macro_dice_present_only": round(macro_dice(a, b, False, allow_crop=allow_crop), 4),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mask-a", required=True)
    p.add_argument("--mask-b", required=True)
    p.add_argument("--json", help="optional path to write the result as JSON")
    p.add_argument("--allow-common-crop", action="store_true",
                   help="crop to the common shape instead of erroring on a size mismatch "
                        "(for the provenance experiment's known padding case only)")
    args = p.parse_args()
    result = compare(args.mask_a, args.mask_b, allow_crop=args.allow_common_crop)
    for k, v in result.items():
        print(f"  {k:28s} {v}")
    if args.json:
        json.dump(result, open(args.json, "w"), indent=2)
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
