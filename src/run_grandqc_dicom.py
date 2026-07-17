"""Run the two GrandQC stages on an IDC DICOM series directory.

    python src/run_grandqc_dicom.py --dicom-dir data/idc/TCGA-AC-A23G-01Z-00-DX1 \
        --output-dir results/dicom/TCGA-AC-A23G --grandqc-dir external/grandqc/01_WSI_inference_OPENSLIDE_QC

DICOM directories are read through wsidicom (correct YBR_ICT color). This is the wrapper
around the fork's wsi_tis_detect.py + main.py; see run_grandqc_svs.py for the SVS arm.
The two wrappers are intentionally identical except for the input, so the comparison holds
code and models fixed and varies only the format.
"""
import argparse
import os
import subprocess
import sys


def run(grandqc_dir: str, slide_folder: str, output_dir: str, mpp: float = 1.5):
    slide_folder, output_dir = os.path.abspath(slide_folder), os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    for step, extra in [
        ("wsi_tis_detect.py", []),
        ("main.py", ["--mpp_model", str(mpp), "--create_geojson", "N"]),
    ]:
        cmd = [sys.executable, step, "--slide_folder", slide_folder,
               "--output_dir", output_dir] + extra
        print("running", " ".join(cmd))
        r = subprocess.run(cmd, cwd=grandqc_dir)
        if r.returncode != 0:
            raise SystemExit(f"{step} exited {r.returncode}")
    print(f"masks in {output_dir}/mask_qc/")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    # A DICOM series is a directory; the parent is what GrandQC scans.
    p.add_argument("--dicom-dir", required=True, help="parent folder containing barcode/ subdirs, "
                                                      "or a single series dir's parent")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--grandqc-dir", default="external/grandqc/01_WSI_inference_OPENSLIDE_QC")
    p.add_argument("--mpp", type=float, default=1.5)
    args = p.parse_args()
    run(args.grandqc_dir, args.dicom_dir, args.output_dir, args.mpp)


if __name__ == "__main__":
    main()
