import uuid

from django.test import SimpleTestCase

from apps.workspace import serializers


class WatchlistReorderInputTests(SimpleTestCase):
    def setUp(self):
        self.ids = [uuid.uuid4(), uuid.uuid4()]

    def serializer(self, values):
        return serializers.WatchlistReorderInputSerializer(
            data={"item_ids": values}, context={"current_item_ids": self.ids}
        )

    def test_reorder_requires_complete_unique_owned_uuid_permutation(self):
        for values in (
            None,
            "abc",
            [],
            [str(self.ids[0])],
            [str(self.ids[0])] * 2,
            [str(self.ids[0]), str(uuid.uuid4())],
            ["bad", str(self.ids[1])],
            [None, str(self.ids[1])],
        ):
            with self.subTest(values=values):
                self.assertFalse(self.serializer(values).is_valid())

    def test_valid_permutation_preserves_client_order(self):
        serializer = self.serializer([str(self.ids[1]), str(self.ids[0])])
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["item_ids"], list(reversed(self.ids))
        )
