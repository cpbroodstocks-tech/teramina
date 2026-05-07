# pylint: disable=redefined-outer-name
"""
Unit tests for feeding recommendation logic.

Covers:
  - Appetite belief (compute_appetite_belief)
  - Ration distribution (_feeding_time_weights)
  - Asymmetric penalty (_asymmetric_ration_adjustment)
  - Sigmoid risk multiplier (_sigmoid_risk_multiplier)
  - Layer selection (blind_feed DOC≤30, rule_v1 DOC>30, ml_v1 DOC≥60)
"""

import math
from unittest.mock import MagicMock, patch

import pytest

# conftest.py handles Django setup

from teramina.feeding.services.appetite_state import (
    compute_appetite_belief,
    DECAY_LAMBDA,
    NEUTRAL_APPETITE,
    NEUTRAL_CONFIDENCE,
)
from teramina.feeding.services.feeding_recommendation_service import (
    _feeding_time_weights,
    _asymmetric_ration_adjustment,
    _sigmoid_risk_multiplier,
    LEFTOVER_HIGH_THRESHOLD,
    LEFTOVER_LOW_THRESHOLD,
    ML_CONFIDENCE_THRESHOLD,
    ML_LAYER_DOC_THRESHOLD,
)
from teramina.helpers.constant_value import Constant


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _fake_realization(doc, feed_given, feed_leftover):
    r = MagicMock()
    r.doc = doc
    r.feed_given = feed_given
    r.feed_leftover = feed_leftover
    return r


# ─── Appetite belief ──────────────────────────────────────────────────────────

class TestComputeAppetiteBelief:
    def test_no_records_returns_neutral(self):
        with patch("teramina.feeding.services.appetite_state.FeedRealization.objects") as mock_qs:
            mock_qs.return_value.only.return_value = []
            result = compute_appetite_belief("cycle_1", doc=5)
        assert result["appetite"] == NEUTRAL_APPETITE
        assert result["confidence"] == NEUTRAL_CONFIDENCE
        assert result["n_observations"] == 0

    def test_all_leftover_zero_returns_max_appetite(self):
        records = [_fake_realization(doc=i, feed_given=10.0, feed_leftover=0.0) for i in range(1, 5)]
        with patch("teramina.feeding.services.appetite_state.FeedRealization.objects") as mock_qs:
            mock_qs.return_value.only.return_value = records
            result = compute_appetite_belief("cycle_1", doc=5)
        assert result["appetite"] == pytest.approx(1.0, abs=0.01)

    def test_all_leftover_full_returns_zero_appetite(self):
        # leftover = all feed given → ratio = 1.0 → appetite_obs = 0
        records = [_fake_realization(doc=i, feed_given=10.0, feed_leftover=10.0) for i in range(1, 5)]
        with patch("teramina.feeding.services.appetite_state.FeedRealization.objects") as mock_qs:
            mock_qs.return_value.only.return_value = records
            result = compute_appetite_belief("cycle_1", doc=5)
        assert result["appetite"] == pytest.approx(0.0, abs=0.01)

    def test_missing_leftover_excluded(self):
        # One record has leftover=None — should be excluded entirely
        records = [
            _fake_realization(doc=3, feed_given=10.0, feed_leftover=None),
            _fake_realization(doc=4, feed_given=10.0, feed_leftover=0.0),
        ]
        with patch("teramina.feeding.services.appetite_state.FeedRealization.objects") as mock_qs:
            mock_qs.return_value.only.return_value = records
            result = compute_appetite_belief("cycle_1", doc=5)
        # Only doc=4 contributes — should be high appetite
        assert result["appetite"] > 0.8
        assert result["n_observations"] == 1

    def test_confidence_scales_with_days(self):
        records = [_fake_realization(doc=i, feed_given=10.0, feed_leftover=1.0) for i in range(1, 4)]
        with patch("teramina.feeding.services.appetite_state.FeedRealization.objects") as mock_qs:
            mock_qs.return_value.only.return_value = records
            result = compute_appetite_belief("cycle_1", doc=4)
        assert result["confidence"] == pytest.approx(3 / 7, abs=0.01)

    def test_confidence_capped_at_one(self):
        records = [_fake_realization(doc=i, feed_given=10.0, feed_leftover=1.0) for i in range(1, 15)]
        with patch("teramina.feeding.services.appetite_state.FeedRealization.objects") as mock_qs:
            mock_qs.return_value.only.return_value = records
            result = compute_appetite_belief("cycle_1", doc=15)
        assert result["confidence"] == 1.0

    def test_recent_observations_weighted_higher(self):
        # Yesterday (doc=9) leftover=0 (high appetite), a week ago (doc=3) leftover=1.0 (zero appetite)
        records = [
            _fake_realization(doc=3, feed_given=10.0, feed_leftover=10.0),  # 6 days ago
            _fake_realization(doc=9, feed_given=10.0, feed_leftover=0.0),   # 1 day ago
        ]
        with patch("teramina.feeding.services.appetite_state.FeedRealization.objects") as mock_qs:
            mock_qs.return_value.only.return_value = records
            result = compute_appetite_belief("cycle_1", doc=10)
        # Recent high-appetite day should dominate → appetite > 0.5
        assert result["appetite"] > 0.5


# ─── Ration distribution ──────────────────────────────────────────────────────

class TestFeedingTimeWeights:
    @pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, 10])
    def test_weights_sum_to_one(self, n):
        weights = _feeding_time_weights(n)
        assert sum(weights) == pytest.approx(1.0, abs=1e-5)

    @pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 6, 10])
    def test_correct_number_of_slots(self, n):
        assert len(_feeding_time_weights(n)) == n

    def test_evening_slot_highest_for_preset_n4(self):
        weights = _feeding_time_weights(4)
        assert weights[-1] == max(weights)

    def test_evening_slot_fixed_at_35_for_n_gt_4(self):
        for n in [5, 6, 7, 10]:
            weights = _feeding_time_weights(n)
            # Last slot should be largest (≈0.35 before normalization)
            assert weights[-1] >= weights[0]


# ─── Asymmetric penalty ───────────────────────────────────────────────────────

class TestAsymmetricRationAdjustment:
    def test_no_leftover_data_conservative_estimate(self):
        base = 10.0
        result = _asymmetric_ration_adjustment(base, appetite=0.5, leftover_ratio=None)
        # multiplier = 0.85 + 0.15*0.5 = 0.925
        assert result == pytest.approx(base * (0.85 + 0.15 * 0.5), abs=0.01)

    def test_overfeeding_reduces_ration(self):
        base = 10.0
        high_leftover = LEFTOVER_HIGH_THRESHOLD + 0.20  # well above threshold
        result = _asymmetric_ration_adjustment(base, appetite=0.5, leftover_ratio=high_leftover)
        assert result < base

    def test_overfeeding_reduction_capped(self):
        base = 10.0
        extreme_leftover = 0.99  # almost all feed left
        result = _asymmetric_ration_adjustment(base, appetite=0.5, leftover_ratio=extreme_leftover)
        # Must not reduce more than MAX_OVERFEEDING_REDUCTION (50%)
        assert result >= base * (1 - Constant.MAX_OVERFEEDING_REDUCTION)

    def test_underfeeding_increases_ration_with_high_appetite(self):
        base = 10.0
        low_leftover = LEFTOVER_LOW_THRESHOLD / 2  # below threshold
        result = _asymmetric_ration_adjustment(base, appetite=0.9, leftover_ratio=low_leftover)
        assert result > base

    def test_underfeeding_increase_capped(self):
        base = 10.0
        result = _asymmetric_ration_adjustment(base, appetite=1.0, leftover_ratio=0.0)
        assert result <= base * Constant.MAX_UNDERFEEDING_BOOST

    def test_acceptable_zone_stays_near_base(self):
        base = 10.0
        mid_leftover = (LEFTOVER_HIGH_THRESHOLD + LEFTOVER_LOW_THRESHOLD) / 2
        result = _asymmetric_ration_adjustment(base, appetite=0.5, leftover_ratio=mid_leftover)
        # Should be within ±10% of base
        assert base * 0.90 <= result <= base * 1.10

    def test_high_appetite_increases_in_acceptable_zone(self):
        base = 10.0
        mid_leftover = (LEFTOVER_HIGH_THRESHOLD + LEFTOVER_LOW_THRESHOLD) / 2
        low_appetite = _asymmetric_ration_adjustment(base, appetite=0.0, leftover_ratio=mid_leftover)
        high_appetite = _asymmetric_ration_adjustment(base, appetite=1.0, leftover_ratio=mid_leftover)
        assert high_appetite >= low_appetite


# ─── Sigmoid risk multiplier ──────────────────────────────────────────────────

class TestSigmoidRiskMultiplier:
    def test_healthy_conditions_near_one(self):
        mult = _sigmoid_risk_multiplier(ration_kg=10.0, biomass_kg=500.0, do_avg=6.5, nh3=0.05)
        assert mult > 0.90, "healthy conditions should barely reduce ration"

    def test_low_do_reduces_ration(self):
        normal = _sigmoid_risk_multiplier(ration_kg=10.0, biomass_kg=500.0, do_avg=6.5, nh3=0.1)
        low_do = _sigmoid_risk_multiplier(ration_kg=10.0, biomass_kg=500.0, do_avg=2.5, nh3=0.1)
        assert low_do < normal

    def test_high_nh3_reduces_ration(self):
        normal = _sigmoid_risk_multiplier(ration_kg=10.0, biomass_kg=500.0, do_avg=6.5, nh3=0.1)
        high_nh3 = _sigmoid_risk_multiplier(ration_kg=10.0, biomass_kg=500.0, do_avg=6.5, nh3=1.5)
        assert high_nh3 < normal

    def test_multiplier_never_below_floor(self):
        # Worst case: tiny DO, huge NH3, high feed rate
        mult = _sigmoid_risk_multiplier(ration_kg=100.0, biomass_kg=100.0, do_avg=0.5, nh3=5.0)
        assert mult >= (1.0 - Constant.MAX_RISK_REDUCTION)

    def test_multiplier_never_above_one(self):
        mult = _sigmoid_risk_multiplier(ration_kg=1.0, biomass_kg=10000.0, do_avg=10.0, nh3=0.0)
        assert mult <= 1.0

    def test_no_biomass_uses_zero_fr(self):
        mult = _sigmoid_risk_multiplier(ration_kg=10.0, biomass_kg=None, do_avg=6.0, nh3=0.1)
        assert 0.0 < mult <= 1.0

    def test_zero_biomass_does_not_crash(self):
        mult = _sigmoid_risk_multiplier(ration_kg=10.0, biomass_kg=0.0, do_avg=6.0, nh3=0.1)
        assert 0.0 < mult <= 1.0


# ─── Layer selection via get_recommendation ───────────────────────────────────

class TestLayerSelection:
    """
    Test that get_recommendation() selects the correct layer based on DOC.
    We mock all DB calls and the ML service so we test decision logic only.
    """

    def _run(self, doc, ml_confidence=0.0):
        from teramina.feeding.services.feeding_recommendation_service import (
            FeedingRecommendationService,
            _get_current_metrics,
            _get_recent_leftover_ratio,
        )
        from teramina.feeding.models.feeding_recommendation_model import FeedingRecommendation

        metrics = {
            "current_doc": doc, "abw": 12.0, "do_avg": 6.0,
            "temp_avg": 29.0, "nh3": 0.1, "biomass": 500.0,
            "total_feed_given": 100.0,
        }
        appetite = {"appetite": 0.7, "confidence": 0.8, "n_observations": 5}

        with (
            patch.object(FeedingRecommendation, "objects") as mock_rec_qs,
            patch("teramina.feeding.services.feeding_recommendation_service._get_current_metrics", return_value=metrics),
            patch("teramina.feeding.services.feeding_recommendation_service._get_recent_leftover_ratio", return_value=0.05),
            patch("teramina.feeding.services.feeding_recommendation_service.compute_appetite_belief", return_value=appetite),
            patch("teramina.feeding.services.feeding_recommendation_service.FeedingMLService.predict") as mock_ml,
            patch("teramina.feeding.models.feeding_recommendation_model.FeedingRecommendation.save"),
        ):
            mock_rec_qs.return_value.first.return_value = None
            if ml_confidence > ML_CONFIDENCE_THRESHOLD:
                mock_ml.return_value = {
                    "recommended_kg": 8.5,
                    "confidence": ml_confidence,
                    "model_version": "xgb_v2",
                    "shap_explanation": "biomass dominant",
                }
            else:
                mock_ml.return_value = {"recommended_kg": 8.5, "confidence": ml_confidence}

            status, response = FeedingRecommendationService.get_recommendation("cycle_1", doc)
        return status, response

    def test_doc_30_uses_blind_feed(self):
        status, response = self._run(doc=30)
        assert status == 200
        assert response.payload["model_layer"] == "blind_feed"

    def test_doc_31_uses_rule_v1(self):
        status, response = self._run(doc=31)
        assert status == 200
        assert response.payload["model_layer"] == "rule_v1"

    def test_doc_60_low_confidence_stays_rule_v1(self):
        status, response = self._run(doc=60, ml_confidence=0.4)
        assert status == 200
        assert response.payload["model_layer"] == "rule_v1"

    def test_doc_60_high_confidence_uses_ml(self):
        status, response = self._run(doc=60, ml_confidence=0.9)
        assert status == 200
        assert response.payload["model_layer"] == "ml_v1"

    def test_ration_is_positive(self):
        _, response = self._run(doc=45)
        assert response.payload["recommended_ration_kg"] > 0

    def test_ration_per_feeding_sums_to_total(self):
        _, response = self._run(doc=45)
        total = response.payload["recommended_ration_kg"]
        per_slot = response.payload["ration_per_feeding"]
        assert sum(per_slot) == pytest.approx(total, abs=0.01)
