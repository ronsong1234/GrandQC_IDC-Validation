"""Query IDC for TCGA H&E slides with codec/scanner/magnification metadata.

    python src/query_idc.py --collection tcga_brca --out config/brca_candidates.csv

Codec (transfer syntax) and scanner (manufacturer) ARE in the IDC index; the photometric
interpretation that pinpoints YBR_ICT is NOT (use inspect_dicom_headers.py for that).
"""
import argparse


def query(collection: str):
    from idc_index import IDCClient
    c = IDCClient()
    c.fetch_index("sm_index")
    return c.sql_query(f"""
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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--collection", default="tcga_brca")
    p.add_argument("--out", default="idc_candidates.csv")
    args = p.parse_args()
    df = query(args.collection)
    df["magnification"] = df["pixel_spacing_mm"].map(lambda x: "20x" if x >= 0.0004 else "40x")
    df.to_csv(args.out, index=False)
    print(f"{len(df)} slides -> {args.out}")
    print(df["transfer_syntax"].value_counts().to_string())


if __name__ == "__main__":
    main()
