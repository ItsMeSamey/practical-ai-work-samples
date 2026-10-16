import unittest
from receipt_demo import extract

VALID = 'Currency: USD\nSUBTOTAL 12.50\nTAX 1.00\nTOTAL 13.50'

class ReceiptValidation(unittest.TestCase):
    def test_exact_decimal_arithmetic(self):
        self.assertEqual(extract('Currency: USD\nSUBTOTAL 0.10\nTAX 0.20\nTOTAL 0.30')['total'], '0.30')
    def test_valid_and_case_insensitive(self):
        self.assertEqual(extract(VALID.lower())['subtotal'], '12.50')
    def test_missing_total_rejected(self):
        with self.assertRaises(ValueError): extract(VALID.replace('TOTAL 13.50',''))
    def test_duplicate_total_rejected(self):
        with self.assertRaises(ValueError): extract(VALID+'\nTOTAL 13.50')
    def test_inconsistent_sum_rejected(self):
        with self.assertRaises(ValueError): extract(VALID.replace('TOTAL 13.50','TOTAL 18.50'))
    def test_ambiguous_digit_is_not_silently_repaired(self):
        with self.assertRaises(ValueError): extract(VALID.replace('TOTAL 13.50','TOTAL 13.5O'))
    def test_missing_currency_rejected(self):
        with self.assertRaises(ValueError): extract(VALID.replace('Currency: USD',''))
    def test_subtotal_cannot_satisfy_total(self):
        with self.assertRaises(ValueError): extract('Currency: USD\nSUBTOTAL 12.50\nTAX 1.00')
    def test_wrong_currency_rejected(self):
        with self.assertRaises(ValueError): extract(VALID.replace('USD','EUR'))

    def test_malformed_duplicate_is_not_ignored(self):
        with self.assertRaises(ValueError): extract(VALID+'\nTOTAL 13.5O')
    def test_conflicting_currency_rejected(self):
        with self.assertRaises(ValueError): extract(VALID+'\nCurrency: EUR')
    def test_extra_currency_suffix_rejected(self):
        with self.assertRaises(ValueError): extract(VALID.replace('USD','USD unknown'))

if __name__ == '__main__': unittest.main()
