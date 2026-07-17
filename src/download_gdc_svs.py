"""Download the original TCGA .svs from GDC for a barcode (the matched-SVS baseline).

The Zenodo reference-mask filename embeds the source .svs filename, so each barcode
resolves to its exact GDC file. The UUID inside the filename is a legacy identifier, not
the GDC file_id — query by file_name and let GDC return the real id.

    python src/download_gdc_svs.py --barcode TCGA-AC-A23G-01Z-00-DX1 \
        --svs-filename "TCGA-AC-A23G-01Z-00-DX1.<UUID>.svs" --out-dir data/gdc
"""
import argparse
import json
import os
import urllib.parse
import urllib.request


def gdc_lookup(svs_filename: str):
    filt = {"op": "=", "content": {"field": "file_name", "value": svs_filename}}
    q = ("https://api.gdc.cancer.gov/files?filters="
         + urllib.parse.quote(json.dumps(filt))
         + "&fields=file_id,file_size,access,md5sum")
    hits = json.loads(urllib.request.urlopen(q, timeout=60).read())["data"]["hits"]
    return hits[0] if hits else None


def download(svs_filename: str, out_dir: str, barcode: str | None = None) -> str:
    os.makedirs(out_dir, exist_ok=True)
    hit = gdc_lookup(svs_filename)
    if hit is None:
        raise SystemExit(f"NOT FOUND on GDC: {svs_filename}")
    dest = os.path.join(out_dir, f"{barcode or svs_filename}.svs")
    if os.path.exists(dest) and os.path.getsize(dest) > 1 << 20:
        print(f"already present: {dest}")
        return dest
    print(f"downloading {hit['file_size']/1e6:.0f} MB (md5 {hit['md5sum']}) ...")
    urllib.request.urlretrieve("https://api.gdc.cancer.gov/data/" + hit["file_id"], dest)
    return dest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--svs-filename", required=True, help="exact GDC .svs filename")
    p.add_argument("--barcode", help="output basename (defaults to the filename)")
    p.add_argument("--out-dir", default="data/gdc")
    args = p.parse_args()
    dest = download(args.svs_filename, args.out_dir, args.barcode)
    print(f"-> {dest}")


if __name__ == "__main__":
    main()
