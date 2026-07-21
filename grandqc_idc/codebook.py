"""The GrandQC mask codebook — the single source of truth for mask value semantics.

Artifact mask values are **1-based**: 0 is the unwritten floor-grid margin (not a class),
1-6 are tissue/artifact classes, 7 is background. This is the encoding that was mislabeled
early in the project; every consumer imports from here so it cannot drift. See CODEBOOK.md.
"""

CLASS_NAMES = {
    0: "Margin (unwritten)",
    1: "Clean tissue",
    2: "Folds",
    3: "Dark spots",
    4: "Pen marks",
    5: "Bubbles/edges",
    6: "Out-of-focus",
    7: "Background",
}

# GrandQC wsi_colors.py palette (RGB). Value v uses PALETTE[v]; margin renders as background.
PALETTE = {
    1: (128, 128, 128), 2: (255, 99, 71), 3: (0, 255, 0), 4: (255, 0, 0),
    5: (255, 0, 255), 6: (75, 0, 130), 7: (255, 255, 255),
}

MARGIN = 0
BACK_CLASS = 7
TISSUE_CLASSES = (1, 2, 3, 4, 5, 6)

# The tissue-DETECTION mask has inverted polarity vs the artifact mask (a frequent bug):
TISSUE_DETECT = {"tissue": 0, "background": 1}
