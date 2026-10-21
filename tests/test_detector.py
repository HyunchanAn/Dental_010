import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.detector import (
    MissingToothDetector,
    MissingSupernumeraryDetector,
    verify_missing_teeth,
    evaluate_missing_teeth_from_boxes,
    estimate_dynamic_midline_x,
)


def make_full_arch_boxes():
    """
    Constructs a synthetic 32-tooth adult dentition layout with 40px tooth width
    and 50px center-to-center spacing per quadrant.
    """
    fdi_labels = []
    boxes = []
    # Upper right (18..11) from x=100 to x=450, Upper left (21..28) from x=500 to x=850
    for i, fdi in enumerate([18, 17, 16, 15, 14, 13, 12, 11]):
        x1 = 100.0 + i * 50.0
        fdi_labels.append(fdi)
        boxes.append([x1, 150.0, x1 + 40.0, 230.0])
    for i, fdi in enumerate([21, 22, 23, 24, 25, 26, 27, 28]):
        x1 = 500.0 + i * 50.0
        fdi_labels.append(fdi)
        boxes.append([x1, 150.0, x1 + 40.0, 230.0])
    # Lower right (48..41) and Lower left (31..38)
    for i, fdi in enumerate([48, 47, 46, 45, 44, 43, 42, 41]):
        x1 = 100.0 + i * 50.0
        fdi_labels.append(fdi)
        boxes.append([x1, 280.0, x1 + 40.0, 360.0])
    for i, fdi in enumerate([31, 32, 33, 34, 35, 36, 37, 38]):
        x1 = 500.0 + i * 50.0
        fdi_labels.append(fdi)
        boxes.append([x1, 280.0, x1 + 40.0, 360.0])
    return fdi_labels, boxes


def test_backward_compatible_set_difference():
    detector = MissingSupernumeraryDetector()
    fdi_labels, _ = make_full_arch_boxes()
    filtered = [f for f in fdi_labels if f not in {16, 38}] + [99]
    res = detector.detect(filtered)
    assert res["missing_teeth"] == [16, 38]
    assert res["supernumerary_or_error"] == [99]


def test_minimum_eight_teeth_safety_guard():
    res = evaluate_missing_teeth_from_boxes(
        detected_fdi_labels=[11, 21, 31, 41],
        boxes=[[450, 150, 490, 230], [500, 150, 540, 230], [500, 280, 540, 360], [450, 280, 490, 360]],
    )
    assert res["verified_missing"] == []
    assert len(res["uncertain_missing"]) == 28
    assert res["details"][0]["status"] == "UNVERIFIED_INSUFFICIENT_TEETH"


def test_spatial_gap_ratio_and_posterior_isolation():
    fdi_labels, boxes = make_full_arch_boxes()
    # Remove #16 (inter-tooth gap between #15 and #17 is 100px = 2.5x tooth width >= 1.55)
    # and remove #38 (posterior 3rd molar -> isolated as uncertain_missing)
    kept_fdi = []
    kept_boxes = []
    for f, b in zip(fdi_labels, boxes):
        if f in {16, 38}:
            continue
        kept_fdi.append(f)
        kept_boxes.append(b)

    res = evaluate_missing_teeth_from_boxes(kept_fdi, kept_boxes)
    assert 16 in res["verified_missing"]
    assert 38 in res["uncertain_missing"]
    assert 38 not in res["verified_missing"]


def test_closed_orthodontic_space_flagged_as_uncertain():
    fdi_labels, boxes = make_full_arch_boxes()
    # Remove #14 and shift #15..#18 mesially so gap between #13 and #15 is closed (45px / 40px = 1.125 < 1.55)
    kept_fdi = []
    kept_boxes = []
    for f, b in zip(fdi_labels, boxes):
        if f == 14:
            continue
        b_copy = list(b)
        if f in {15, 16, 17, 18}:
            b_copy[0] += 55.0
            b_copy[2] += 55.0
        kept_fdi.append(f)
        kept_boxes.append(b_copy)

    res = evaluate_missing_teeth_from_boxes(kept_fdi, kept_boxes, gap_ratio_threshold=1.55)
    assert 14 not in res["verified_missing"]
    assert 14 in res["uncertain_missing"]
    midline = estimate_dynamic_midline_x(kept_fdi, kept_boxes)
    assert 470.0 <= midline <= 520.0
