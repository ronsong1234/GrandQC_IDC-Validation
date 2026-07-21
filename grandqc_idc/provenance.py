"""Provenance helpers: resolve/checksum slides and read the codec that OpenSlide mis-decodes.

These use only the standard library + pydicom (lazy), so they work without idc-index or the
heavy readers installed. IDC index queries live in :mod:`grandqc_idc.idc`.
"""
from __future__ import annotations

import io
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

_S3 = "https://idc-open-data.s3.amazonaws.com/"
_NS = "{http://s3.amazonaws.com/doc/2006-03-01/}"


def gdc_lookup(svs_filename: str) -> dict | None:
    """GDC file record for an exact TCGA .svs filename (open access, no auth)."""
    filt = {"op": "=", "content": {"field": "file_name", "value": svs_filename}}
    q = ("https://api.gdc.cancer.gov/files?filters="
         + urllib.parse.quote(json.dumps(filt))
         + "&fields=file_id,file_size,access,md5sum")
    hits = json.loads(urllib.request.urlopen(q, timeout=60).read())["data"]["hits"]
    return hits[0] if hits else None


def gdc_svs_by_barcode(barcode: str) -> dict | None:
    """Resolve a TCGA barcode to its open-access diagnostic .svs on GDC (no Zenodo needed).

    The UUID in the .svs filename is a legacy identifier, not the GDC file_id — we query by
    patient + data_format and pick the file whose name starts with the full barcode.
    """
    patient = "-".join(barcode.split("-")[:3])
    filt = {"op": "and", "content": [
        {"op": "=", "content": {"field": "cases.submitter_id", "value": patient}},
        {"op": "=", "content": {"field": "data_format", "value": "SVS"}},
        {"op": "=", "content": {"field": "access", "value": "open"}}]}
    q = ("https://api.gdc.cancer.gov/files?filters="
         + urllib.parse.quote(json.dumps(filt))
         + "&fields=file_id,file_name,file_size,md5sum&size=100")
    hits = json.loads(urllib.request.urlopen(q, timeout=60).read())["data"]["hits"]
    for h in hits:
        if h["file_name"].startswith(barcode + "."):
            return h
    return None


def gdc_download(file_id: str, dest: str) -> str:
    urllib.request.urlretrieve("https://api.gdc.cancer.gov/data/" + file_id, dest)
    return dest


def photometric_for_series(crdc_series_uuid: str, timeout: int = 60) -> str:
    """PhotometricInterpretation of an IDC series, from ~300 KB of one instance's header.

    This is the value that distinguishes OpenSlide-vulnerable YBR_ICT slides from safe RGB
    ones — it is not in the IDC index, so it must be read from the header. No pixel data is
    downloaded (HTTP range request against the public idc-open-data S3 bucket).
    """
    import pydicom

    listing = urllib.request.urlopen(
        f"{_S3}?list-type=2&prefix={crdc_series_uuid}/", timeout=timeout).read().decode()
    keys = [(e.find(_NS + "Key").text, int(e.find(_NS + "Size").text))
            for e in ET.fromstring(listing).findall(_NS + "Contents")]
    key = sorted(keys, key=lambda x: -x[1])[0][0]           # largest instance = base VOLUME
    req = urllib.request.Request(_S3 + key, headers={"Range": "bytes=0-300000"})
    data = urllib.request.urlopen(req, timeout=timeout).read()
    ds = pydicom.dcmread(io.BytesIO(data), stop_before_pixels=True, force=True)
    return str(ds.get("PhotometricInterpretation"))
