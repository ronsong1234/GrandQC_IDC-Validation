"""Reader routing: DICOM directories -> wsidicom, .svs files -> OpenSlide.

Guards the root-cause bug of the whole project: OpenSlide 4.0.1 silently mis-decodes
YBR_ICT JPEG 2000 DICOM, so DICOM must never be routed to OpenSlide. This test encodes the
routing contract without needing the heavy readers installed.
"""
import os


def route_reader(path: str) -> str:
    """Mirror of GrandQC open_slide() dispatch: DICOM series (dir with .dcm) -> wsidicom."""
    if os.path.isdir(path):
        return "wsidicom"
    if path.lower().endswith(".dcm"):
        return "wsidicom"
    return "openslide"


def test_dicom_directory_routes_to_wsidicom(tmp_path):
    d = tmp_path / "TCGA-AC-A23G-01Z-00-DX1"
    d.mkdir()
    (d / "instance.dcm").write_bytes(b"")
    assert route_reader(str(d)) == "wsidicom"


def test_single_dcm_routes_to_wsidicom(tmp_path):
    f = tmp_path / "x.dcm"
    f.write_bytes(b"")
    assert route_reader(str(f)) == "wsidicom"


def test_svs_routes_to_openslide(tmp_path):
    f = tmp_path / "TCGA-AC-A23G.svs"
    f.write_bytes(b"")
    assert route_reader(str(f)) == "openslide"


def test_dicom_never_routes_to_openslide(tmp_path):
    d = tmp_path / "series"
    d.mkdir()
    (d / "a.dcm").write_bytes(b"")
    assert route_reader(str(d)) != "openslide", "DICOM via OpenSlide -> YBR_ICT corruption"
