"""Read PhotometricInterpretation from IDC DICOM slides WITHOUT downloading pixels.

Uses HTTP range requests against the public ``idc-open-data`` S3 bucket to fetch only
the header of one instance per series. This is how the YBR_ICT prevalence was measured
(Notebook 03) — the value that distinguishes the OpenSlide-vulnerable slides is *not* in
the IDC index and must be read from the header.

    python src/inspect_dicom_headers.py --collection tcga_brca --transfer-syntax "JPEG 2000"
"""
import argparse
import io
import urllib.request
import xml.etree.ElementTree as ET

import pydicom

S3 = "https://idc-open-data.s3.amazonaws.com/"
NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"


def photometric_for_series(crdc_uuid: str, timeout: int = 60) -> str:
    """PhotometricInterpretation of a series, read from ~300 KB of one instance."""
    listing = urllib.request.urlopen(
        f"{S3}?list-type=2&prefix={crdc_uuid}/", timeout=timeout
    ).read().decode()
    keys = [(e.find(NS + "Key").text, int(e.find(NS + "Size").text))
            for e in ET.fromstring(listing).findall(NS + "Contents")]
    # largest instance = base VOLUME; header (0028,0004) precedes PixelData
    key = sorted(keys, key=lambda x: -x[1])[0][0]
    req = urllib.request.Request(S3 + key, headers={"Range": "bytes=0-300000"})
    data = urllib.request.urlopen(req, timeout=timeout).read()
    ds = pydicom.dcmread(io.BytesIO(data), stop_before_pixels=True, force=True)
    return str(ds.get("PhotometricInterpretation"))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--collection", default="tcga_brca")
    p.add_argument("--transfer-syntax", default="JPEG 2000",
                   help="substring filter on transfer_syntax_name (JPEG 2000 slides "
                        "are the only ones that can be YBR_ICT)")
    p.add_argument("--out", default="ybr_ict_prevalence.csv")
    args = p.parse_args()

    from idc_index import IDCClient
    c = IDCClient()
    c.fetch_index("sm_index")
    rows = c.sql_query(f"""
        SELECT s.ContainerIdentifier AS bc, i.crdc_series_uuid AS crdc
        FROM index i JOIN sm_index s ON i.SeriesInstanceUID = s.SeriesInstanceUID
        WHERE i.collection_id = '{args.collection}'
          AND i.transfer_syntax_name LIKE '%{args.transfer_syntax}%'
          AND s.ContainerIdentifier LIKE '%-DX%'
    """)
    import csv
    from collections import Counter
    results = {}
    for _, r in rows.iterrows():
        try:
            results[r.bc] = photometric_for_series(r.crdc)
        except Exception as exc:  # noqa: BLE001 - transient S3 errors are recorded
            results[r.bc] = f"ERR:{type(exc).__name__}"
        print(f"  {r.bc}: {results[r.bc]}")
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["barcode", "photometric_interpretation"])
        w.writerows(results.items())
    ybr = sum("YBR" in v for v in results.values())
    print(f"\nYBR_ICT: {ybr}/{len(results)}  ({Counter(results.values())})")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
