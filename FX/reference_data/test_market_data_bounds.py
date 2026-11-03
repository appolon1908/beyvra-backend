from types import SimpleNamespace

from django.test import SimpleTestCase

from reference_data.market_data_views import _bounded_int


class MarketDataBoundsTests(SimpleTestCase):
    def test_bounds_reject_nonpositive_and_noninteger_values(self):
        for value in ("-10", "0", "garbage", "1.5"):
            with self.subTest(value=value):
                parsed, error = _bounded_int(
                    SimpleNamespace(query_params={"limit": value}),
                    name="limit",
                    default=100,
                    maximum=500,
                )
                self.assertIsNone(parsed)
                self.assertEqual(error.status_code, 400)

    def test_valid_limits_are_preserved(self):
        for value in ("1", "100", "500"):
            parsed, error = _bounded_int(
                SimpleNamespace(query_params={"limit": value}),
                name="limit",
                default=100,
                maximum=500,
            )
            self.assertEqual(parsed, int(value))
            self.assertIsNone(error)

    def test_existing_upper_clamp_is_preserved(self):
        parsed, error = _bounded_int(
            SimpleNamespace(query_params={"limit": "501"}),
            name="limit",
            default=100,
            maximum=500,
        )
        self.assertEqual(parsed, 500)
        self.assertIsNone(error)
