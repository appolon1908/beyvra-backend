"""Exercise portfolio risk arithmetic without replacing the decision under test.

The portfolio loader and open-order query are persistence boundaries. They are
substituted here so these checks need no PostgreSQL migration or live provider.
"""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from .portfolio_api import PortfolioRiskView


@override_settings(
    SIMULATED_TRADING_ENABLED=True,
    DEPLOYMENT_ENV="test",
    REAL_TRADING_ENABLED=False,
    EXTERNAL_EXECUTION_ENABLED=False,
    REAL_MONEY_ENABLED=False,
)
class PortfolioRiskAuthorityUnitTests(SimpleTestCase):
    def risk(self, values, *, cash="160", available="150"):
        positions = [{"market_value": value} for value in values]
        market_value = sum(
            (Decimal(value) for value in values if value is not None), Decimal("0")
        )
        account = SimpleNamespace(total_balance=Decimal(cash))
        portfolio = (
            account, positions, Decimal(available), market_value,
            Decimal("0"), Decimal("0"),
        )
        request = SimpleNamespace(user=SimpleNamespace(pk="portfolio-fixture"))
        with (
            patch.object(PortfolioRiskView, "portfolio", return_value=portfolio),
            patch("apps.valuation.portfolio_api.TradingOrder.objects.filter") as orders,
        ):
            orders.return_value.count.return_value = 0
            response = PortfolioRiskView().get(request)
        self.assertEqual(response.status_code, 200)
        return response.data

    def test_offsetting_long_and_short_preserve_gross_exposure(self):
        result = self.risk(["120", "-80"])

        self.assertEqual(Decimal(result["equity"]), Decimal("200"))
        self.assertEqual(Decimal(result["gross_exposure"]), Decimal("200"))
        self.assertEqual(Decimal(result["net_exposure"]), Decimal("40"))
        self.assertEqual(Decimal(result["gross_exposure_ratio"]), Decimal("1"))
        self.assertEqual(Decimal(result["largest_position_ratio"]), Decimal("0.6"))
        self.assertEqual(Decimal(result["cash_ratio"]), Decimal("0.75"))
        self.assertEqual(result["valuation_quality"], "COMPLETE")

    def test_zero_or_negative_equity_does_not_fabricate_ratios(self):
        for cash in ("-40", "-50"):
            with self.subTest(cash=cash):
                result = self.risk(["120", "-80"], cash=cash, available="0")
                self.assertIsNone(result["gross_exposure_ratio"])
                self.assertIsNone(result["cash_ratio"])
                self.assertEqual(
                    Decimal(result["largest_position_ratio"]), Decimal("0.6")
                )

    def test_unpriced_positions_are_excluded_with_partial_quality(self):
        result = self.risk(["100", None], cash="100", available="100")

        self.assertEqual(Decimal(result["gross_exposure"]), Decimal("100"))
        self.assertEqual(Decimal(result["net_exposure"]), Decimal("100"))
        self.assertEqual(result["valuation_quality"], "PARTIAL")
        self.assertTrue(result["methodology"]["unpriced_positions_excluded"])
        self.assertIsNone(result["value_at_risk"])
        self.assertIsNone(result["stress_loss"])
        self.assertEqual(
            result["advanced_risk_reason"], "CERTIFIED_HISTORY_AND_POLICY_REQUIRED"
        )

    def test_unavailable_prices_do_not_fabricate_concentration(self):
        result = self.risk([None, None])

        self.assertEqual(result["valuation_quality"], "UNAVAILABLE")
        self.assertEqual(Decimal(result["gross_exposure"]), Decimal("0"))
        self.assertEqual(Decimal(result["net_exposure"]), Decimal("0"))
        self.assertIsNone(result["largest_position_ratio"])

    def test_empty_portfolio_remains_distinct_from_unavailable_prices(self):
        result = self.risk([])

        self.assertEqual(result["valuation_quality"], "EMPTY")
        self.assertIsNone(result["largest_position_ratio"])
        self.assertTrue(result["simulation"])
        self.assertFalse(result["live_trading_enabled"])
