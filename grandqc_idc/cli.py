"""Command-line entry points (registered as console_scripts in pyproject.toml).

    grandqc-compare         --mask-a A.png --mask-b B.png [--json out] [--allow-common-crop]
    grandqc-overlay         --mask-a A.png --mask-b B.png --out fig.png [--allow-common-crop]
    grandqc-inspect-headers --collection tcga_brca [--transfer-syntax "JPEG 2000"]
"""
from __future__ import annotations

import argparse
import csv
import json


def compare_main(argv=None):
    from .metrics import compare
    p = argparse.ArgumentParser(prog="grandqc-compare",
                                description="Compare two GrandQC masks.")
    p.add_argument("--mask-a", required=True)
    p.add_argument("--mask-b", required=True)
    p.add_argument("--json", help="write the result as JSON")
    p.add_argument("--allow-common-crop", action="store_true",
                   help="crop to common shape instead of erroring on a size mismatch")
    a = p.parse_args(argv)
    result = compare(a.mask_a, a.mask_b, allow_crop=a.allow_common_crop)
    for k, v in result.items():
        print(f"  {k:28s} {v}")
    if a.json:
        json.dump(result, open(a.json, "w"), indent=2)
        print(f"\nwrote {a.json}")


def overlay_main(argv=None):
    from .overlays import difference_figure
    p = argparse.ArgumentParser(prog="grandqc-overlay",
                                description="Three-panel difference figure for two masks.")
    p.add_argument("--mask-a", required=True)
    p.add_argument("--mask-b", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--label-a", default="A")
    p.add_argument("--label-b", default="B")
    p.add_argument("--allow-common-crop", action="store_true")
    a = p.parse_args(argv)
    difference_figure(a.mask_a, a.mask_b, a.out, a.label_a, a.label_b,
                      allow_crop=a.allow_common_crop)
    print(f"wrote {a.out}")


def inspect_headers_main(argv=None):
    from .idc import query_he_slides
    from .provenance import photometric_for_series
    p = argparse.ArgumentParser(prog="grandqc-inspect-headers",
                                description="Measure YBR_ICT prevalence from DICOM headers.")
    p.add_argument("--collection", default="tcga_brca")
    p.add_argument("--transfer-syntax", default="JPEG 2000")
    p.add_argument("--out", default="ybr_ict_prevalence.csv")
    a = p.parse_args(argv)
    df = query_he_slides(a.collection)
    df = df[df["transfer_syntax"].str.contains(a.transfer_syntax, na=False)]
    from collections import Counter
    results = {}
    for _, r in df.iterrows():
        try:
            results[r.barcode] = photometric_for_series(r.crdc_series_uuid)
        except Exception as exc:  # noqa: BLE001
            results[r.barcode] = f"ERR:{type(exc).__name__}"
        print(f"  {r.barcode}: {results[r.barcode]}")
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["barcode", "photometric_interpretation"])
        w.writerows(sorted(results.items()))
    ybr = sum("YBR" in v for v in results.values())
    print(f"\nYBR_ICT: {ybr}/{len(results)}  ({dict(Counter(results.values()))})")
    print(f"wrote {a.out}")
