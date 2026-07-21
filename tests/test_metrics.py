"""Metric functions against tiny arrays with hand-computed answers.

Guards the class of bug that produced 0.34 / 1.0 nonsense early in the project: a metric
that silently mishandles the margin (0) or the tissue set.
"""

import numpy as np

from grandqc_idc import agreement, macro_dice, tissue_iou, tissue_mask, tw_dice  # noqa: E402


def test_tissue_mask_excludes_margin_and_background():
    m = np.array([[0, 1, 7], [2, 6, 7]])
    # tissue = classes 1-6; margin(0) and background(7) excluded
    assert tissue_mask(m).tolist() == [[False, True, False], [True, True, False]]


def test_identical_masks_agree_100():
    m = np.array([[1, 2, 7], [3, 7, 1]])
    ag = agreement(m, m.copy())
    assert ag["whole_image"] == 100.0
    assert ag["within_shared_tissue"] == 100.0
    assert tissue_iou(m, m.copy()) == 1.0


def test_margin_excluded_from_whole_image():
    a = np.array([[0, 1, 7]])       # first pixel is margin
    b = np.array([[5, 1, 7]])       # differs only under the margin
    # margin pixel is dropped -> the two remaining pixels agree -> 100%
    assert agreement(a, b)["whole_image"] == 100.0


def test_tissue_iou_half():
    a = np.array([[1, 1, 7, 7]])    # tissue = 2 px
    b = np.array([[1, 7, 7, 1]])    # tissue = 2 px, overlap = 1, union = 3
    assert abs(tissue_iou(a, b) - 1 / 3) < 1e-9


def test_tw_dice_perfect_and_disjoint():
    a = np.array([[1, 1, 7, 7]])
    assert tw_dice(a, a.copy()) == 1.0
    b = np.array([[7, 7, 1, 1]])   # tissue disjoint from a -> Dice 0
    assert tw_dice(a, b) == 0.0


def test_macro_dice_convention_differs():
    # class present in one mask only -> the two conventions diverge
    a = np.array([[1, 1, 2]])
    b = np.array([[1, 1, 1]])      # class 2 absent in b; class present-in-either
    hi = macro_dice(a, b, absent_as_zero=False)
    lo = macro_dice(a, b, absent_as_zero=True)
    assert lo < hi  # absent-as-zero drags the mean down
