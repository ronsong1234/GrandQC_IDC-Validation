"""grandqc_idc — reproducible QC validation for GrandQC on IDC DICOM whole-slide images.

Public API (import from the top level):

    from grandqc_idc import compare, agreement, tissue_iou, tw_dice, macro_dice
    from grandqc_idc import gdc_svs_by_barcode, photometric_for_series, route_reader
    from grandqc_idc import CLASS_NAMES, TISSUE_CLASSES, BACK_CLASS, MARGIN

See CODEBOOK.md for mask semantics and docs/ for the findings this validates.
"""
from .codebook import (BACK_CLASS, CLASS_NAMES, MARGIN, PALETTE, TISSUE_CLASSES,
                       TISSUE_DETECT)
from .metrics import (MaskShapeMismatch, agreement, colorize, compare, dice, load_mask,
                      macro_dice, sha256, tissue_iou, tissue_mask, tw_dice)
from .provenance import (gdc_download, gdc_lookup, gdc_svs_by_barcode,
                         photometric_for_series)
from .readers import route_reader, run_grandqc, run_grandqc_dicom, run_grandqc_svs

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # codebook
    "CLASS_NAMES", "PALETTE", "MARGIN", "BACK_CLASS", "TISSUE_CLASSES", "TISSUE_DETECT",
    # metrics
    "compare", "agreement", "tissue_iou", "tw_dice", "macro_dice", "dice", "tissue_mask",
    "colorize", "load_mask", "sha256", "MaskShapeMismatch",
    # provenance
    "gdc_svs_by_barcode", "gdc_lookup", "gdc_download", "photometric_for_series",
    # readers
    "route_reader", "run_grandqc", "run_grandqc_dicom", "run_grandqc_svs",
]
