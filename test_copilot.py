import unittest
from validators import verhoeff_valid, check_pan, check_aadhaar, check_ifsc
from extract import parse_document
from checks import run_checks, verdict

PAN = "INCOME TAX DEPARTMENT\nName: Aditi Verma\nDate of Birth: 14/03/1998\nPAN: BZXPV4821K\nAddress: 22 Lakeview Road, Indore, Madhya Pradesh 452001\n"
AAD = "AADHAAR\nName: Aditi Verma\nDOB: 14/03/1998\nAadhaar No: 2999 8887 7760\nAddress: 22 Lakeview Road, Indore, Madhya Pradesh 452001\n"
BANK = "STATEMENT\nName: Aditi Verma\nAccount No: 33112244556\nIFSC: SBIN0004521\nAddress: 22 Lakeview Road, Indore\n"


class TestValidators(unittest.TestCase):
    def test_verhoeff(self):
        self.assertTrue(verhoeff_valid("299988877760"))
        self.assertFalse(verhoeff_valid("299988877761"))

    def test_pan(self):
        self.assertEqual(check_pan("BZXPV4821K"), [])
        self.assertTrue(check_pan("BZXP14821K"))   # 4th char digit
        self.assertTrue(check_pan("BZXPV4821"))    # too short

    def test_ifsc(self):
        self.assertEqual(check_ifsc("SBIN0004521"), [])
        self.assertTrue(check_ifsc("SB1N00452X"))


class TestChecks(unittest.TestCase):
    def _docs(self, pan=PAN, aad=AAD, bank=BANK):
        return [parse_document("pan", pan), parse_document("aadhaar", aad),
                parse_document("bank_statement", bank)]

    def test_clean_is_clear(self):
        self.assertEqual(verdict(run_checks(self._docs())), "NO_FLAGS_NOT_VERIFIED")

    def test_dob_mismatch(self):
        bad = AAD.replace("14/03/1998", "14/03/1997")
        flags = run_checks(self._docs(aad=bad))
        self.assertIn("DOB_MISMATCH", {f.code for f in flags})
        self.assertEqual(verdict(flags), "REVIEW_FLAGS")

    def test_bank_name_mismatch(self):
        bad = BANK.replace("Aditi Verma", "Rohit Malhotra")
        flags = run_checks(self._docs(bank=bad))
        self.assertIn("BANK_NAME_MISMATCH", {f.code for f in flags})

    def test_fabricated_aadhaar_flagged_not_dropped(self):
        bad = AAD.replace("2999 8887 7760", "1234 5678 9012")
        flags = run_checks(self._docs(aad=bad))
        self.assertIn("AADHAAR_CHECKSUM", {f.code for f in flags})

    def test_common_surnames_do_not_hide_mismatch(self):
        bad = BANK.replace("Aditi Verma", "Rohit Verma")
        flags = run_checks(self._docs(bank=bad))
        self.assertIn("BANK_NAME_MISMATCH", {f.code for f in flags})


if __name__ == "__main__":
    unittest.main()

class TestEvidenceGaps(unittest.TestCase):
    def test_empty_never_clears(self):
        self.assertEqual(verdict(run_checks([])), "REVIEW_FLAGS")
    def test_missing_ifsc_is_not_dropped(self):
        doc = parse_document("bank_statement", BANK.replace("SBIN0004521", "SB1N00452X"))
        self.assertIn("IFSC_FORMAT", {f.code for f in run_checks([doc])})
    def test_invalid_calendar_date(self):
        doc = parse_document("pan", PAN.replace("14/03/1998", "31/02/1998"))
        self.assertIn("DOB_INVALID", {f.code for f in run_checks([doc])})
