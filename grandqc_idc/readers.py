"""Reader routing and GrandQC invocation.

The one safety-critical rule of the project: **DICOM series go to wsidicom, never
OpenSlide** (OpenSlide 4.0.1 silently mis-decodes YBR_ICT JPEG 2000 — see docs/findings.md
§2). `route_reader` encodes that contract; `run_grandqc` invokes the pinned fork's two
inference stages identically for either input, so a comparison varies only the format.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile


def route_reader(path: str) -> str:
    """Which backend GrandQC's open_slide() uses: DICOM (dir or .dcm) -> wsidicom, else OpenSlide."""
    if os.path.isdir(path):
        return "wsidicom"
    if path.lower().endswith(".dcm"):
        return "wsidicom"
    return "openslide"


def run_grandqc(slide_folder: str, output_dir: str, scripts_dir: str,
                mpp: float = 1.5, create_geojson: bool = False) -> str:
    """Run the two GrandQC stages (tissue detection + artifact segmentation) on a folder.

    `scripts_dir` is the pinned fork's ``01_WSI_inference_OPENSLIDE_QC`` directory. Returns
    the mask_qc output directory. Identical for DICOM and SVS inputs — only the format
    (hence the reader GrandQC selects internally) differs.
    """
    slide_folder, output_dir = os.path.abspath(slide_folder), os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    for step, extra in [
        ("wsi_tis_detect.py", []),
        ("main.py", ["--mpp_model", str(mpp),
                     "--create_geojson", "Y" if create_geojson else "N"]),
    ]:
        cmd = [sys.executable, step, "--slide_folder", slide_folder,
               "--output_dir", output_dir] + extra
        r = subprocess.run(cmd, cwd=scripts_dir)
        if r.returncode != 0:
            raise RuntimeError(f"{step} exited {r.returncode}")
    return os.path.join(output_dir, "mask_qc")


def run_grandqc_dicom(dicom_parent: str, output_dir: str, scripts_dir: str, mpp: float = 1.5):
    """Run GrandQC on IDC DICOM series (parent folder of barcode subdirs)."""
    return run_grandqc(dicom_parent, output_dir, scripts_dir, mpp)


def run_grandqc_svs(svs_file: str, output_dir: str, scripts_dir: str, mpp: float = 1.5):
    """Run GrandQC on a single .svs (staged in a temp folder GrandQC can scan)."""
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(svs_file, tmp)
        return run_grandqc(tmp, output_dir, scripts_dir, mpp)
