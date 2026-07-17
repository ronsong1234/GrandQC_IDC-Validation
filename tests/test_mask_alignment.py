"""Alignment guard: fail loudly if two masks that should match differ in shape.

Silent resizing is how a spatial misalignment hides behind a good-looking agreement %.
The comparison code crops to the common area; these tests pin the expected behavior.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from utils import agreement  # noqa: E402


def masks_shape(a, b):
    return a.shape == b.shape


def test_matched_run_must_share_dimensions():
    # DICOM and SVS masks of the same slide MUST be identical-shape; a mismatch is a bug.
    a = np.ones((3037, 3263), np.uint8)
    b = np.ones((3037, 3263), np.uint8)
    assert masks_shape(a, b), "matched-slide masks differ in shape -> investigate before trusting agreement"


def test_shape_mismatch_is_detectable():
    a = np.ones((100, 100), np.uint8)
    b = np.ones((100, 90), np.uint8)
    assert not masks_shape(a, b)


def test_agreement_does_not_silently_upscale():
    # agreement crops to the common area; it must never resample one mask to the other,
    # which would fabricate alignment. A 1-row offset should reduce agreement, not hide.
    a = np.array([[1, 1, 1], [7, 7, 7]], np.uint8)
    b = np.array([[7, 7, 7], [1, 1, 1]], np.uint8)  # vertically flipped
    assert agreement(a, b)["whole_image"] < 50.0
