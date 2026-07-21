"""IDC index queries and DICOM download (require the optional `idc-index` dependency)."""
from __future__ import annotations

import os
import shutil


def _client():
    from idc_index import IDCClient
    c = IDCClient()
    c.fetch_index("sm_index")
    return c


def query_he_slides(collection: str = "tcga_brca"):
    """H&E diagnostic slides for a collection with codec/scanner/magnification metadata.

    transfer_syntax and Manufacturer ARE in the index; photometric interpretation (YBR_ICT)
    is not — use :func:`grandqc_idc.provenance.photometric_for_series` for that.
    """
    df = _client().sql_query(f"""
        SELECT s.ContainerIdentifier AS barcode,
               i.SeriesInstanceUID   AS series_instance_uid,
               i.crdc_series_uuid    AS crdc_series_uuid,
               i.transfer_syntax_name AS transfer_syntax,
               i.Manufacturer        AS manufacturer,
               s.ObjectiveLensPower  AS objective_power,
               s.min_PixelSpacing_2sf AS pixel_spacing_mm,
               ROUND(i.series_size_MB, 1) AS size_mb
        FROM index i JOIN sm_index s ON i.SeriesInstanceUID = s.SeriesInstanceUID
        WHERE i.collection_id = '{collection}'
          AND array_to_string(s.staining_usingSubstance_CodeMeaning, ', ') LIKE '%hematoxylin%'
          AND s.ContainerIdentifier LIKE '%-DX%'
        ORDER BY i.series_size_MB ASC
    """)
    df["magnification"] = df["pixel_spacing_mm"].map(lambda x: "20x" if x >= 0.0004 else "40x")
    return df


def download_dicom(barcodes, out_dir: str = "data/idc"):
    """Download IDC DICOM series for `barcodes`, renaming each UID dir to its barcode."""
    import pandas as pd  # noqa: F401 - kept for parity/typing
    c = _client()
    os.makedirs(out_dir, exist_ok=True)
    meta = c.sql_query(
        "SELECT s.ContainerIdentifier AS bc, i.SeriesInstanceUID AS suid "
        "FROM index i JOIN sm_index s ON i.SeriesInstanceUID = s.SeriesInstanceUID "
        "WHERE s.ContainerIdentifier IN ({})".format(",".join(f"'{b}'" for b in barcodes))
    ).drop_duplicates("bc")
    c.download_from_selection(downloadDir=out_dir,
                              seriesInstanceUID=meta["suid"].tolist(),
                              dirTemplate="%SeriesInstanceUID")
    for _, r in meta.iterrows():
        src, dst = os.path.join(out_dir, r.suid), os.path.join(out_dir, r.bc)
        if os.path.isdir(src) and not os.path.isdir(dst):
            os.rename(src, dst)
        elif os.path.isdir(src):
            shutil.rmtree(src)
    return out_dir
