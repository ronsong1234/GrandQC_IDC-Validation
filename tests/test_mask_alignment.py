"""Alignment guard: fail loudly if two masks that should match differ in shape.

Silent resizing is how a spatial misalignment hides behind a good-looking agreement %.
The comparison code crops to the common area; these tests pin the expected behavior.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from utils import MaskShapeMismatch, agreement  # noqa: E402


def test_mismatched_shapes_raise_by_default():
    # The primary SVS-DICOM comparison must NOT silently crop a size mismatch.
    a = np.ones((100, 100), np.uint8)
    b = np.ones((100, 90), np.uint8)
    with pytest.raises(MaskShapeMismatch):
        agreement(a, b)


def test_allow_crop_opt_in_still_computes():
    # The provenance experiment's historical-padding case may crop, on explicit opt-in.
    a = np.ones((100, 100), np.uint8)
    b = np.ones((100, 90), np.uint8)
    with pytest.warns(UserWarning):
        result = agreement(a, b, allow_crop=True)
    assert result["whole_image"] == 100.0


def test_matched_run_shares_dimensions():
    a = np.ones((3037, 3263), np.uint8)
    b = np.ones((3037, 3263), np.uint8)
    assert agreement(a, b)["whole_image"] == 100.0  # same shape -> no raise


def test_agreement_does_not_silently_upscale():
    # agreement crops to the common area; it must never resample one mask to the other,
    # which would fabricate alignment. A 1-row offset should reduce agreement, not hide.
    a = np.array([[1, 1, 1], [7, 7, 7]], np.uint8)
    b = np.array([[7, 7, 7], [1, 1, 1]], np.uint8)  # vertically flipped
    assert agreement(a, b)["whole_image"] < 50.0
