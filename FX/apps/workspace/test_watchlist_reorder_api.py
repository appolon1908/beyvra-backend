import uuid
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from apps.workspace.models import Watchlist, WatchlistItem
from users.models import User
from integrations.models import Organization, OrganizationMembership


SIMULATION = override_settings(
    DEPLOYMENT_ENV="test",
    SIMULATED_TRADING_ENABLED=True,
    REAL_TRADING_ENABLED=False,
    EXTERNAL_EXECUTION_ENABLED=False,
    REAL_MONEY_ENABLED=False,
)


@SIMULATION
class WatchlistAlertsApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email=f"wl-test-{uuid.uuid4()}@example.invalid",
            phone_number=f"+1202{uuid.uuid4().int % 10000000:07d}",
            password="testpassword",
        )
        self.org = Organization.objects.create(name=f"Org {uuid.uuid4()}")
        OrganizationMembership.objects.create(user=self.user, organization=self.org)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.watchlist = Watchlist.objects.create(
            organization=self.org,
            user=self.user,
            name="Main Watchlist",
            is_default=True,
        )
        self.item1 = WatchlistItem.objects.create(
            watchlist=self.watchlist, instrument_id="BTC-USD", sort_order=0
        )
        self.item2 = WatchlistItem.objects.create(
            watchlist=self.watchlist, instrument_id="ETH-USD", sort_order=1
        )

    def test_reorder_watchlist_items_optimistic_concurrency_success(self):
        res = self.client.patch(
            f"/api/v1/watchlists/{self.watchlist.id}/items/reorder",
            {
                "expected_version": 1,
                "ordered_item_ids": [str(self.item2.id), str(self.item1.id)],
            },
            format="json",
            HTTP_IF_MATCH='"1"',
        )
        self.assertEqual(res.status_code, 200)
        self.watchlist.refresh_from_db()
        self.assertEqual(self.watchlist.version, 2)
        self.assertEqual(
            [item["id"] for item in res.json()["items"]],
            [str(self.item2.id), str(self.item1.id)],
        )

    def test_reorder_watchlist_items_optimistic_concurrency_conflict(self):
        res = self.client.patch(
            f"/api/v1/watchlists/{self.watchlist.id}/items/reorder",
            {
                "expected_version": 99,
                "ordered_item_ids": [str(self.item2.id), str(self.item1.id)],
            },
            format="json",
            HTTP_IF_MATCH='"99"',
        )
        self.assertEqual(res.status_code, 412)
        self.assertEqual(
            res.json()["error"]["code"],
            "OPTIMISTIC_CONCURRENCY_CONFLICT",
        )

    def test_invalid_permutations_do_not_mutate_items_or_version(self):
        original = [(self.item1.pk, 0), (self.item2.pk, 1)]
        for ids in (
            [],
            [str(self.item1.pk)],
            [str(self.item1.pk)] * 2,
            ["not-a-uuid"],
            [str(uuid.uuid4()), str(self.item2.pk)],
        ):
            with self.subTest(ids=ids):
                response = self.client.patch(
                    f"/api/v1/watchlists/{self.watchlist.pk}/items/reorder",
                    {"expected_version": 1, "ordered_item_ids": ids},
                    format="json",
                    HTTP_IF_MATCH='"1"',
                )
                self.assertEqual(response.status_code, 400)
                self.watchlist.refresh_from_db()
                self.assertEqual(self.watchlist.version, 1)
                self.assertEqual(
                    list(self.watchlist.items.values_list("pk", "sort_order")), original
                )

    def test_reorder_requires_a_version_precondition(self):
        response = self.client.patch(
            f"/api/v1/watchlists/{self.watchlist.pk}/items/reorder",
            {"ordered_item_ids": [str(self.item2.pk), str(self.item1.pk)]},
            format="json",
        )
        self.assertEqual(response.status_code, 428)
