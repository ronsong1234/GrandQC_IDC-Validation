"""Download an IDC DICOM series (or a whole cohort CSV) via idc-index.

    python src/download_idc_dicom.py --barcode TCGA-AC-A23G-01Z-00-DX1 --out-dir data/idc
    python src/download_idc_dicom.py --cohort config/five_slide_demo.csv --out-dir data/idc

Series are downloaded to <out-dir>/<SeriesInstanceUID>/ then renamed to the barcode, so
downstream code (and run_grandqc_dicom.py) can find them by barcode.
"""
import argparse
import os
import shutil


def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--barcode")
    g.add_argument("--cohort", help="CSV with a tcga_barcode column")
    p.add_argument("--out-dir", default="data/idc")
    args = p.parse_args()

    from idc_index import IDCClient
    import pandas as pd
    c = IDCClient()
    c.fetch_index("sm_index")

    if args.barcode:
        barcodes = [args.barcode]
    else:
        barcodes = pd.read_csv(args.cohort)["tcga_barcode"].tolist()

    os.makedirs(args.out_dir, exist_ok=True)
    meta = c.sql_query(
        "SELECT s.ContainerIdentifier AS bc, i.SeriesInstanceUID AS suid "
        "FROM index i JOIN sm_index s ON i.SeriesInstanceUID = s.SeriesInstanceUID "
        "WHERE s.ContainerIdentifier IN ({})".format(
            ",".join(f"'{b}'" for b in barcodes))
    ).drop_duplicates("bc")

    c.download_from_selection(
        downloadDir=args.out_dir,
        seriesInstanceUID=meta["suid"].tolist(),
        dirTemplate="%SeriesInstanceUID",
    )
    for _, r in meta.iterrows():
        src, dst = os.path.join(args.out_dir, r.suid), os.path.join(args.out_dir, r.bc)
        if os.path.isdir(src) and not os.path.isdir(dst):
            os.rename(src, dst)
        elif os.path.isdir(src):
            shutil.rmtree(src)
        print(f"  {r.bc}")
    print(f"-> {args.out_dir}/")


if __name__ == "__main__":
    main()
