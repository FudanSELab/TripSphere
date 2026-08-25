from __future__ import annotations

import json
import unittest
from pathlib import Path


SEEDED_DIR = Path(__file__).resolve().parents[1] / "data" / "seeded" / "shanghai"


class SeededContractsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.hotels = json.loads((SEEDED_DIR / "hotels.json").read_text())
        cls.room_types = json.loads((SEEDED_DIR / "room_types.json").read_text())
        cls.spus = json.loads((SEEDED_DIR / "spus.json").read_text())
        cls.inventories = json.loads((SEEDED_DIR / "inventories.json").read_text())

    def test_room_types_reference_real_hotels(self) -> None:
        hotel_ids = {hotel["_id"] for hotel in self.hotels}
        missing = [
            room_type["_id"]
            for room_type in self.room_types
            if room_type["hotelId"] not in hotel_ids
        ]

        self.assertEqual([], missing)
        self.assertGreater(len(hotel_ids), 0)

    def test_hotel_room_spus_reference_real_room_types(self) -> None:
        room_type_ids = {room_type["_id"] for room_type in self.room_types}
        hotel_room_spus = [
            spu for spu in self.spus if spu["resourceType"] == "HOTEL_ROOM"
        ]
        missing = [
            spu["_id"] for spu in hotel_room_spus if spu["resourceId"] not in room_type_ids
        ]

        self.assertEqual([], missing)
        self.assertGreater(len(hotel_room_spus), 0)

    def test_inventory_rows_reference_real_skus(self) -> None:
        sku_ids = {
            sku["id"]
            for spu in self.spus
            for sku in spu.get("skus", [])
        }
        missing = [
            inventory["id"]
            for inventory in self.inventories
            if inventory["skuId"] not in sku_ids
        ]

        self.assertEqual([], missing)
        self.assertGreater(len(self.inventories), 0)


if __name__ == "__main__":
    unittest.main()
