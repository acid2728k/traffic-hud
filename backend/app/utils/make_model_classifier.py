from typing import Tuple, Optional


def classify_make_model(frame, bbox: Tuple[int, int, int, int]) -> Tuple[Optional[str], float]:
    """
    Basic make/model classifier.
    In MVP returns "Unknown" with low confidence.
    Architecturally prepared for model improvement.
    """
    # TODO: Integration with make/model classification model
    # For now return Unknown
    return None, 0.0

