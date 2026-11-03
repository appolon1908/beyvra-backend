"""Cash projection must distinguish unsettled cash from active reservations."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.trading.api.account_projections_views import AccountBalancesProjectionView


class AccountCashAuthorityUnitTests(SimpleTestCase):
    def test_distinct_pending_cash_and_reservations_reconcile(self):
        account = SimpleNamespace(
            id="account-fixture", quote_currency="USD",
            total_balance=Decimal("10000"), pending_balance=Decimal("500"),
        )
        request = SimpleNamespace(user=SimpleNamespace(pk="subject-fixture"))
        with (
            patch("apps.trading.api.account_projections_views.simulation_authorized", return_value=True),
            patch("apps.trading.api.account_projections_views.SimulatedAccount.objects.filter") as accounts,
            patch("apps.trading.api.account_projections_views.SimulatedFinancialAdapter.available_quote", return_value=Decimal("8000")),
        ):
            accounts.return_value.first.return_value = account
            result = AccountBalancesProjectionView().get(request, account.id).data
        for field, expected in {
            "cash": "10000", "settled_cash": "9500", "unsettled_cash": "500",
            "reserved_cash": "1500", "available_cash": "8000", "buying_power": "8000",
        }.items():
            with self.subTest(field=field):
                self.assertEqual(Decimal(result[field]), Decimal(expected))
        self.assertEqual(
            Decimal(result["settled_cash"]) + Decimal(result["unsettled_cash"]),
            Decimal(result["cash"]),
        )
