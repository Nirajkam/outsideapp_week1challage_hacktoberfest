import csv
import io
import tempfile
import unittest
from pathlib import Path

from receipt_sorter import csv_bytes, organize_receipt, parse_receipt_json


class ReceiptSorterTests(unittest.TestCase):
    def test_parse_normalizes_receipt_fields(self):
        receipt = parse_receipt_json(
            '```json\n{"vendor":"  Acme  Cafe ","date":"2026-02-03",'
            '"amount":"1,234.50","currency":"usd","category":"meals",'
            '"description":" Lunch   meeting "}\n```'
        )

        self.assertEqual(receipt["vendor"], "Acme Cafe")
        self.assertEqual(receipt["date"], "2026-02-03")
        self.assertEqual(receipt["amount"], "1234.50")
        self.assertEqual(receipt["currency"], "USD")
        self.assertEqual(receipt["category"], "Meals")
        self.assertEqual(receipt["description"], "Lunch meeting")

    def test_parse_uses_safe_defaults_for_invalid_values(self):
        receipt = parse_receipt_json(
            '{"vendor":"","date":"not-a-date","amount":"NaN","currency":"US",'
            '"category":"made up","description":""}'
        )

        self.assertEqual(receipt["vendor"], "Unknown vendor")
        self.assertEqual(receipt["date"], "")
        self.assertEqual(receipt["amount"], "")
        self.assertEqual(receipt["currency"], "")
        self.assertEqual(receipt["category"], "Other")

    def test_organize_keeps_original_extension_and_avoids_overwrite(self):
        receipt = {
            "vendor": "Acme / Cafe",
            "date": "2026-02-03",
            "amount": "12.50",
            "currency": "USD",
            "category": "Meals",
        }
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_dir = Path(temporary_dir)
            first = organize_receipt(output_dir, "../receipt.pdf", b"first", receipt)
            second = organize_receipt(output_dir, "../receipt.pdf", b"second", receipt)

            self.assertEqual(first, "Meals/2026/Acme_Cafe_2026-02-03_12.50_USD.pdf")
            self.assertEqual(second, "Meals/2026/Acme_Cafe_2026-02-03_12.50_USD_2.pdf")
            self.assertEqual((output_dir / first).read_bytes(), b"first")
            self.assertEqual((output_dir / second).read_bytes(), b"second")

    def test_csv_has_header_and_escapes_commas(self):
        data = csv_bytes(
            [
                {
                    "vendor": "Acme, Inc.",
                    "date": "2026-02-03",
                    "amount": "12.50",
                    "currency": "USD",
                    "category": "Meals",
                    "description": "",
                    "source_file": "receipt.pdf",
                    "sorted_path": "Meals/2026/receipt.pdf",
                }
            ]
        )
        rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"))))
        self.assertEqual(rows[0]["vendor"], "Acme, Inc.")
        self.assertEqual(rows[0]["sorted_path"], "Meals/2026/receipt.pdf")


if __name__ == "__main__":
    unittest.main()
