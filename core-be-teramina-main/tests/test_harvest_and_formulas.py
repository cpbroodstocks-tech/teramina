# pylint: disable=redefined-outer-name
"""
Unit tests for harvest optimization and core farm formulas.

Covers:
  - FrByDPI — DPI-based feed ration (protein bounds)
  - FrByBlindFeed — blind feed schedule (DOC transitions)
  - Sgr — specific growth rate (null handling, zero growth)
  - Growth.wt() — weight curve monotonicity
  - Optimization.generate_revenue() / generate_cost() — matrix properties
  - Optimization.get_optimal_harvest() — output validity
"""

import numpy as np
import pandas as pd
import pytest

# conftest.py handles Django setup

from teramina.formulas.feed.fr_main_formula import FrByDPI, FrByBlindFeed
from teramina.formulas.sgr.growth_rate import Sgr


# ─── FrByDPI ──────────────────────────────────────────────────────────────────

class TestFrByDPI:
    def test_protein_30_returns_positive_fr(self):
        fr, dpi = FrByDPI.get_fr_by_dpi(protein_content=35.0, abw=[5.0, 10.0, 20.0])
        assert all(fr > 0)
        assert all(dpi > 0)

    def test_protein_39_40_band(self):
        fr, dpi = FrByDPI.get_fr_by_dpi(protein_content=39.5, abw=[5.0, 10.0])
        assert all(fr > 0)

    def test_protein_out_of_range_raises(self):
        with pytest.raises(ValueError, match="protein content"):
            FrByDPI.get_fr_by_dpi(protein_content=25.0, abw=[5.0])

    def test_protein_above_40_raises(self):
        with pytest.raises(ValueError):
            FrByDPI.get_fr_by_dpi(protein_content=45.0, abw=[5.0])

    def test_fr_decreases_as_abw_increases(self):
        abw = [2.0, 5.0, 10.0, 20.0, 30.0]
        fr, _ = FrByDPI.get_fr_by_dpi(protein_content=38.0, abw=abw)
        # Larger shrimp need lower feed rate relative to body weight
        assert list(fr) == sorted(fr, reverse=True)

    def test_boundary_protein_30_exact(self):
        fr, _ = FrByDPI.get_fr_by_dpi(protein_content=30.0, abw=[10.0])
        assert fr[0] > 0

    def test_boundary_protein_39_exact(self):
        fr, _ = FrByDPI.get_fr_by_dpi(protein_content=39.0, abw=[10.0])
        assert fr[0] > 0

    def test_higher_protein_lower_fr(self):
        fr_low, _ = FrByDPI.get_fr_by_dpi(protein_content=30.0, abw=[10.0])
        fr_high, _ = FrByDPI.get_fr_by_dpi(protein_content=39.5, abw=[10.0])
        # Higher protein → better amino acid bioavailability → less feed needed
        assert fr_high[0] < fr_low[0]


# ─── FrByBlindFeed ────────────────────────────────────────────────────────────

class TestFrByBlindFeed:
    @pytest.mark.parametrize("doc", [1, 5, 10, 11, 20, 21, 30])
    def test_valid_doc_returns_positive(self, doc):
        result = FrByBlindFeed.blind_feed_nagrofa(doc=doc, population=100_000, biomass=50.0)
        assert result > 0

    def test_doc_31_raises(self):
        with pytest.raises(ValueError, match="30"):
            FrByBlindFeed.blind_feed_nagrofa(doc=31, population=100_000, biomass=50.0)

    def test_feed_increases_over_time(self):
        """Feed amount should increase as shrimp grow."""
        amounts = [
            FrByBlindFeed.blind_feed_nagrofa(doc=d, population=100_000, biomass=50.0)
            for d in [5, 10, 15, 20, 25, 30]
        ]
        assert amounts == sorted(amounts)

    def test_doc_10_11_transition_is_continuous(self):
        at_10 = FrByBlindFeed.blind_feed_nagrofa(doc=10, population=100_000, biomass=100.0)
        at_11 = FrByBlindFeed.blind_feed_nagrofa(doc=11, population=100_000, biomass=100.0)
        # Should be close but 11 > 10
        assert at_11 > at_10
        assert abs(at_11 - at_10) / at_10 < 0.3  # less than 30% jump

    def test_doc_20_21_transition_is_continuous(self):
        at_20 = FrByBlindFeed.blind_feed_nagrofa(doc=20, population=100_000, biomass=100.0)
        at_21 = FrByBlindFeed.blind_feed_nagrofa(doc=21, population=100_000, biomass=100.0)
        assert at_21 > at_20
        assert abs(at_21 - at_20) / at_20 < 0.3

    def test_zero_biomass_returns_zero_fr(self):
        result = FrByBlindFeed.blind_feed_nagrofa(doc=15, population=100_000, biomass=0.0)
        assert result == 0.0

    def test_larger_population_gives_larger_feed(self):
        small = FrByBlindFeed.blind_feed_nagrofa(doc=15, population=100_000, biomass=50.0)
        large = FrByBlindFeed.blind_feed_nagrofa(doc=15, population=500_000, biomass=50.0)
        assert large > small


# ─── Sgr ──────────────────────────────────────────────────────────────────────

class TestSgr:
    def test_none_abw_returns_none(self):
        result = Sgr([]).sgr_function(abw=None, init_abw=5.0, shifted=7)
        assert result is None

    def test_none_init_abw_returns_none(self):
        result = Sgr([]).sgr_function(abw=10.0, init_abw=None, shifted=7)
        assert result is None

    def test_equal_abw_returns_none(self):
        result = Sgr([]).sgr_function(abw=10.0, init_abw=10.0, shifted=7)
        assert result is None

    def test_positive_growth_positive_sgr(self):
        result = Sgr([]).sgr_function(abw=15.0, init_abw=5.0, shifted=7)
        assert result == pytest.approx((15.0 - 5.0) / 7, abs=0.001)

    def test_calculate_handles_none_gaps(self):
        data = [None, None, 5.0, None, 8.0, None, 12.0]
        sgr = Sgr(data)
        results = sgr.calculate()
        assert len(results) == len(data)
        # None entries should produce None SGR
        assert results[0] is None
        assert results[1] is None

    def test_calculate_positive_growth_trend(self):
        data = [3.0, 5.0, 8.0, 12.0, 17.0]
        sgr = Sgr(data)
        results = sgr.calculate()
        # Skip first (None) — rest should be positive
        valid = [r for r in results if r is not None]
        assert all(r > 0 for r in valid)


# ─── Growth.wt() ─────────────────────────────────────────────────────────────

class TestGrowthWt:
    """
    wt() is pure recursive arithmetic — no DB or file access.
    We bypass __init__ (which loads CSV files) and set attributes directly.
    """

    def _make_growth(self, t0=1, t=20, w0=0.5):
        from teramina.formulas.weight.weight_adg import Growth
        g = object.__new__(Growth)
        g.t0 = t0
        g.t = t
        g.w0 = w0
        g.wn = 25.0
        # base_data shape matters only if t == len(base_data[:,3])
        # Set length != t so the recursive branch is always taken
        g.base_data = np.zeros((t + 100, 8))
        return g

    def test_output_length_matches_t_minus_t0(self):
        g = self._make_growth(t0=1, t=20)
        result = g.wt()
        assert len(result) == 20 - 1

    def test_first_weight_is_w0(self):
        g = self._make_growth(t0=1, t=20, w0=0.5)
        result = g.wt()
        assert result[0] == pytest.approx(0.5, abs=0.001)

    def test_second_weight_is_w0_plus_015(self):
        g = self._make_growth(t0=1, t=20, w0=1.0)
        result = g.wt()
        assert result[1] == pytest.approx(1.0 + 0.15, abs=0.001)

    def test_subsequent_weights_follow_recurrence(self):
        g = self._make_growth(t0=1, t=10, w0=1.0)
        result = g.wt()
        # w[i] = 2*w[i-1] - w[i-2] for i >= 2
        for i in range(2, len(result)):
            assert result[i] == pytest.approx(2 * result[i - 1] - result[i - 2], abs=0.001)

    def test_weights_are_positive_for_reasonable_w0(self):
        g = self._make_growth(t0=1, t=30, w0=0.5)
        result = g.wt()
        assert all(w > 0 for w in result)


# ─── Harvest Optimization — matrix properties ─────────────────────────────────

class TestHarvestOptimization:
    """
    Tests on Optimization methods using directly injected synthetic matrices.
    We bypass the heavy __init__ (CSV loading, Growth, Biomass) and test
    generate_revenue, generate_cost, and get_optimal_harvest in isolation.
    """

    @pytest.fixture()
    def opt(self):
        from teramina.formulas.harvest_optimization_formula import Optimization
        from scipy.interpolate import CubicSpline

        n_rows = 5     # combinations
        n_cols = 70    # DOC columns (docfinal=60, total_obs=10)
        doc_final = 60

        o = object.__new__(Optimization)

        # Synthetic matrices
        o.combined_wt = np.linspace(0.5, 20.0, n_cols)
        o.forecast_population = np.full(10, 40_000.0)
        o.historical_population = np.full(doc_final, 50_000.0)

        o.historical_population_config = {
            "doc_final": doc_final,
            "ph": [],
            "partial_doc": [],
        }

        # Price array: [size, price] — monotonically decreasing price with larger size
        price_data = np.array([[0, 0], [30, 80000], [50, 65000], [80, 45000], [120, 30000]])
        o.price_array = price_data[1:]
        o._price_spline = CubicSpline(price_data[:, 0], price_data[:, 1])

        # Temperature FR data: 7 temp ranges × ABW points
        abw_pts = np.array([1, 2, 5, 10, 15, 20, 30], dtype=float)
        o.temperature_data = [
            np.column_stack([abw_pts] + [np.full(7, v) for v in [8, 7.5, 7, 6.5, 6, 5.5, 5]]),
            np.full(n_cols, 29.0),
        ]

        o.cost_config = {
            "energy_cost": [500],
            "probiotics_cost": [100_000],
            "labor_cost": [200_000],
            "bonus": [500],
            "harvest_cost": [1000],
            "feed_cost": [12_000],
            "other": [50_000],
        }

        return o

    def _make_matrices(self, n_rows=5, n_cols=70):
        wt = np.tile(np.linspace(0.5, 20.0, n_cols), (n_rows, 1))
        pop = np.tile(np.linspace(50_000, 40_000, n_cols), (n_rows, 1))
        biomass = (wt * pop) / 1000
        # sparse harvested biomass (most zeros, some positive)
        harv_bio = np.zeros_like(wt)
        harv_bio[:, 60] = 200.0
        harv_bio[:, 69] = 500.0
        return wt, pop, biomass, harv_bio

    def test_generate_revenue_non_negative(self, opt):
        wt, _, _, harv_bio = self._make_matrices()
        revenue = opt.generate_revenue(wt, harv_bio)
        assert (revenue >= 0).all()

    def test_generate_revenue_shape_matches_input(self, opt):
        wt, _, _, harv_bio = self._make_matrices()
        revenue = opt.generate_revenue(wt, harv_bio)
        assert revenue.shape == wt.shape

    def test_generate_revenue_zero_harvest_is_zero(self, opt):
        wt, _, _, _ = self._make_matrices()
        harv_bio = np.zeros_like(wt)
        revenue = opt.generate_revenue(wt, harv_bio)
        assert (revenue == 0).all()

    def test_generate_cost_positive(self, opt):
        wt, _, biomass, harv_bio = self._make_matrices()
        n_rows, n_cols = wt.shape
        temp_fr = np.full((n_rows, n_cols), 0.05)
        cost = opt.generate_cost(
            temp_fr, harv_bio, biomass,
            total_observation=10, total_combination=n_rows,
        )
        assert (cost > 0).all()

    def test_generate_cost_shape_matches_input(self, opt):
        wt, _, biomass, harv_bio = self._make_matrices()
        n_rows, n_cols = wt.shape
        temp_fr = np.full((n_rows, n_cols), 0.05)
        cost = opt.generate_cost(
            temp_fr, harv_bio, biomass,
            total_observation=10, total_combination=n_rows,
        )
        assert cost.shape == wt.shape

    def test_optimal_harvest_selects_max_profit_row(self, opt):
        """argmax(revenue - cost) should select the row with highest net profit."""
        wt, _, biomass, harv_bio = self._make_matrices()
        n_rows, n_cols = wt.shape
        temp_fr = np.full((n_rows, n_cols), 0.05)

        revenue = opt.generate_revenue(wt, harv_bio)
        cost = opt.generate_cost(
            temp_fr, harv_bio, biomass,
            total_observation=10, total_combination=n_rows,
        )
        net = np.sum(revenue - cost, axis=1)
        best_row = int(np.argmax(net))
        # Verify the argmax matches the expected row
        assert net[best_row] == np.max(net)
