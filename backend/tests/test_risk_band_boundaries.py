import pytest

from app.models.guardian import RiskBand
from app.services.risk_engine import classify_risk_score


@pytest.mark.parametrize(
    ("score", "expected_band", "expected_action"),
    [
        (0, RiskBand.LOW, "ALLOW_ROLLOUT"),
        (29.99, RiskBand.LOW, "ALLOW_ROLLOUT"),
        (30, RiskBand.MODERATE, "PROCEED_WITH_CANARY"),
        (49.99, RiskBand.MODERATE, "PROCEED_WITH_CANARY"),
        (50, RiskBand.HIGH, "MANUAL_APPROVAL_REQUIRED"),
        (74.99, RiskBand.HIGH, "MANUAL_APPROVAL_REQUIRED"),
        (75, RiskBand.CRITICAL, "MANUAL_APPROVAL_REQUIRED"),
        (100, RiskBand.CRITICAL, "MANUAL_APPROVAL_REQUIRED"),
    ],
)
def test_risk_band_boundaries(score, expected_band, expected_action):
    assert classify_risk_score(score) == (expected_band, expected_action)
