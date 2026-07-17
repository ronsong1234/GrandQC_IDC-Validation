"""Run the two GrandQC stages on an original .svs file (the matched-SVS baseline).

    python src/run_grandqc_svs.py --svs-file data/gdc/TCGA-AC-A23G.svs \
        --output-dir results/svs/TCGA-AC-A23G --grandqc-dir external/grandqc/01_WSI_inference_OPENSLIDE_QC

.svs files are read through OpenSlide (GrandQC's open_slide() dispatches on input type).
Identical scripts, models and MPP to run_grandqc_dicom.py — only the input format differs.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile


def run(grandqc_dir: str, svs_file: str, output_dir: str, mpp: float = 1.5):
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    # GrandQC scans a folder; stage the single .svs in a temp folder of its own.
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(svs_file, tmp)
        for step, extra in [
            ("wsi_tis_detect.py", []),
            ("main.py", ["--mpp_model", str(mpp), "--create_geojson", "N"]),
        ]:
            cmd = [sys.executable, step, "--slide_folder", tmp,
                   "--output_dir", output_dir] + extra
            print("running", " ".join(cmd))
            r = subprocess.run(cmd, cwd=grandqc_dir)
            if r.returncode != 0:
                raise SystemExit(f"{step} exited {r.returncode}")
    print(f"masks in {output_dir}/mask_qc/")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--svs-file", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--grandqc-dir", default="external/grandqc/01_WSI_inference_OPENSLIDE_QC")
    p.add_argument("--mpp", type=float, default=1.5)
    args = p.parse_args()
    run(args.grandqc_dir, args.svs_file, args.output_dir, args.mpp)


if __name__ == "__main__":
    main()
