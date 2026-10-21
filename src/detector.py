from typing import List, Dict, Any, Optional
import numpy as np

ALL_PERMANENT_FDI = {
    11, 12, 13, 14, 15, 16, 17, 18,
    21, 22, 23, 24, 25, 26, 27, 28,
    31, 32, 33, 34, 35, 36, 37, 38,
    41, 42, 43, 44, 45, 46, 47, 48,
}

POSTERIOR_DISTAL_TEETH = {18, 28, 38, 48, 17, 27, 37, 47}


def estimate_dynamic_midline_x(
    detected_fdi_labels: List[int],
    boxes: List[List[float]],
    img_width: int = 1024,
) -> float:
    """
    Estimates the dental arch midline X-coordinate dynamically from central incisors
    (FDI 11, 21, 31, 41) if available, falling back to the median X-center of all boxes
    or img_width / 2.0.
    """
    if not boxes:
        return float(img_width) / 2.0

    central_xs = []
    all_xs = []
    for fdi, box in zip(detected_fdi_labels, boxes):
        cx = (float(box[0]) + float(box[2])) / 2.0
        all_xs.append(cx)
        if fdi in {11, 21, 31, 41}:
            central_xs.append(cx)

    if central_xs:
        return float(np.mean(central_xs))
    if all_xs:
        return float(np.median(all_xs))
    return float(img_width) / 2.0


def verify_missing_teeth(
    detected_fdi_labels: List[int],
    boxes: List[List[float]],
    img_width: int = 1024,
    img_height: int = 512,
    midline_x: Optional[float] = None,
    min_teeth_guard: int = 8,
    r_gap_threshold: float = 0.65,
    gap_ratio_threshold: float = 1.55,
) -> Dict[str, Any]:
    """
    Unified 2-stage missing tooth heuristic combining:
    1) Set-difference candidate identification against 32 permanent FDI teeth.
    2) Minimum detected teeth safety guard (< 8 teeth -> defer verification).
    3) Posterior distal tooth isolation (FDI #17/#18/#27/#28/#37/#38/#47/#48 -> uncertain_missing).
    4) Dynamic midline estimation and adjacent tooth center/span gap ratio verification
       (r_gap > 0.65 or center-to-center gap_ratio >= 1.55 * mean adjacent width).
    """
    detected_set = set(int(x) for x in detected_fdi_labels)
    candidate_missing = sorted(list(ALL_PERMANENT_FDI - detected_set))
    supernumerary = sorted(list(detected_set - ALL_PERMANENT_FDI))

    if not boxes or len(boxes) == 0:
        return {
            "verified_missing": [],
            "uncertain_missing": candidate_missing,
            "supernumerary_or_error": supernumerary,
            "midline_x": float(midline_x) if midline_x is not None else float(img_width) / 2.0,
            "details": [
                {
                    "status": "UNVERIFIED_NO_TEETH_DETECTED",
                    "reason": "No teeth detected in image. Missing teeth analysis requires teeth boundaries.",
                }
            ],
        }

    resolved_midline_x = (
        float(midline_x)
        if midline_x is not None
        else estimate_dynamic_midline_x(detected_fdi_labels, boxes, img_width=img_width)
    )

    if len(boxes) < min_teeth_guard:
        return {
            "verified_missing": [],
            "uncertain_missing": candidate_missing,
            "supernumerary_or_error": supernumerary,
            "midline_x": resolved_midline_x,
            "details": [
                {
                    "status": "UNVERIFIED_INSUFFICIENT_TEETH",
                    "reason": (
                        f"Only {len(boxes)} teeth detected (threshold: {min_teeth_guard}). "
                        "Risk of image truncation or severe occlusion."
                    ),
                }
            ],
        }

    fdi_to_box: Dict[int, List[float]] = {}
    for fdi, box in zip(detected_fdi_labels, boxes):
        fdi_to_box[int(fdi)] = [float(c) for c in box[:4]]

    widths = [max(1.0, float(b[2]) - float(b[0])) for b in boxes]
    avg_tooth_width = float(np.mean(widths)) if widths else 50.0

    verified_missing: List[int] = []
    uncertain_missing: List[int] = []
    details: List[Dict[str, Any]] = []

    for missing_fdi in candidate_missing:
        if missing_fdi in POSTERIOR_DISTAL_TEETH:
            uncertain_missing.append(missing_fdi)
            details.append(
                {
                    "fdi": missing_fdi,
                    "status": "UNCERTAIN_DISTAL_MISSING",
                    "reason": "Outer distal adjacent tooth absent (Posterior region)",
                }
            )
            continue

        pos = missing_fdi % 10
        if pos > 1:
            mesial_fdi = missing_fdi - 1
        else:
            # Contralateral central incisor across the midline (11<->21, 31<->41)
            q = missing_fdi // 10
            contralateral_q = {1: 2, 2: 1, 3: 4, 4: 3}.get(q, q)
            mesial_fdi = contralateral_q * 10 + 1

        distal_fdi = missing_fdi + 1 if pos < 8 else None

        left_box = fdi_to_box.get(mesial_fdi)
        right_box = fdi_to_box.get(distal_fdi) if distal_fdi else None

        if left_box is not None and right_box is not None:
            left_center_x = (left_box[0] + left_box[2]) / 2.0
            right_center_x = (right_box[0] + right_box[2]) / 2.0
            gap_distance = abs(right_center_x - left_center_x)

            local_adj_width = (
                (left_box[2] - left_box[0]) + (right_box[2] - right_box[0])
            ) / 2.0
            r_gap = gap_distance / avg_tooth_width if avg_tooth_width > 0 else 0.0
            gap_ratio = gap_distance / local_adj_width if local_adj_width > 0 else 0.0

            if gap_ratio >= gap_ratio_threshold or r_gap > r_gap_threshold:
                verified_missing.append(missing_fdi)
                details.append(
                    {
                        "fdi": missing_fdi,
                        "status": "VERIFIED_MISSING",
                        "r_gap": round(float(r_gap), 3),
                        "gap_ratio": round(float(gap_ratio), 3),
                        "gap_distance": round(float(gap_distance), 1),
                    }
                )
            else:
                uncertain_missing.append(missing_fdi)
                details.append(
                    {
                        "fdi": missing_fdi,
                        "status": "UNCERTAIN_DRIFT_OR_IMPACTION",
                        "r_gap": round(float(r_gap), 3),
                        "gap_ratio": round(float(gap_ratio), 3),
                    }
                )
        else:
            uncertain_missing.append(missing_fdi)
            details.append(
                {
                    "fdi": missing_fdi,
                    "status": "UNCERTAIN_INSUFFICIENT_ADJACENT",
                }
            )

    return {
        "verified_missing": verified_missing,
        "uncertain_missing": uncertain_missing,
        "supernumerary_or_error": supernumerary,
        "midline_x": resolved_midline_x,
        "details": details,
    }


def evaluate_missing_teeth_from_boxes(
    detected_fdi_labels: List[int],
    boxes: List[List[float]],
    img_width: int = 1024,
    img_height: int = 512,
    midline_x: Optional[float] = None,
    min_teeth_guard: int = 8,
    gap_ratio_threshold: float = 1.55,
) -> Dict[str, Any]:
    """
    Evaluates missing and supernumerary teeth using bounding-box spatial gap ratios
    (gap_ratio >= 1.55 across mesial/distal neighbors) and minimum tooth count guard (< 8).
    """
    return verify_missing_teeth(
        detected_fdi_labels=detected_fdi_labels,
        boxes=boxes,
        img_width=img_width,
        img_height=img_height,
        midline_x=midline_x,
        min_teeth_guard=min_teeth_guard,
        r_gap_threshold=gap_ratio_threshold,
        gap_ratio_threshold=gap_ratio_threshold,
    )


class MissingToothDetector:
    def __init__(self):
        """
        Dental_010: Missing & Supernumerary Teeth Detection Module
        Provides both backward-compatible 32-tooth set-difference detection and
        2-stage spatial gap-ratio verification (unified with dental_010_heuristic.py).
        """
        self.standard_adult_teeth = set(ALL_PERMANENT_FDI)

    def detect(
        self,
        detected_fdi_list: List[int],
        boxes: Optional[List[List[float]]] = None,
        img_width: int = 1024,
        img_height: int = 512,
        midline_x: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Classifies missing teeth and supernumerary teeth from detected FDI labels
        and optional bounding boxes.
        """
        detected_set = set(int(x) for x in detected_fdi_list)
        missing_teeth = sorted(list(self.standard_adult_teeth - detected_set))
        supernumerary = sorted(list(detected_set - self.standard_adult_teeth))

        result: Dict[str, Any] = {
            "missing_teeth": missing_teeth,
            "supernumerary_or_error": supernumerary,
        }

        if boxes is not None:
            spatial = verify_missing_teeth(
                detected_fdi_labels=detected_fdi_list,
                boxes=boxes,
                img_width=img_width,
                img_height=img_height,
                midline_x=midline_x,
            )
            result.update(spatial)

        return result


MissingSupernumeraryDetector = MissingToothDetector
