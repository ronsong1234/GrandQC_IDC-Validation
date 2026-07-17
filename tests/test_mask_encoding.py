"""The GrandQC artifact-mask codebook: 1-based, 0 = margin, 7 = background.

Guards against the 0-based/1-based confusion that mislabeled every class early on.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from utils import BACK_CLASS, CLASS_NAMES, MARGIN, PALETTE, TISSUE_CLASSES, tissue_mask  # noqa: E402


def test_codebook_constants():
    assert MARGIN == 0
    assert BACK_CLASS == 7
    assert TISSUE_CLASSES == (1, 2, 3, 4, 5, 6)
    assert CLASS_NAMES[1] == "Clean tissue"
    assert CLASS_NAMES[7] == "Background"


def test_margin_is_not_a_class():
    assert 0 not in TISSUE_CLASSES
    assert 0 not in PALETTE  # margin has no palette color; it renders as background


def test_palette_covers_all_real_classes():
    for c in list(TISSUE_CLASSES) + [BACK_CLASS]:
        assert c in PALETTE


def test_clean_tissue_is_class_one_not_zero():
    m = np.array([[0, 1]])          # 0 = margin, 1 = clean tissue
    assert not tissue_mask(m)[0, 0]  # margin is NOT tissue
    assert tissue_mask(m)[0, 1]      # class 1 IS tissue
