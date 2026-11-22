import csv, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import google_contacts as gc


class TestFields(unittest.TestCase):
    def test_swapped(self):
        self.assertEqual(gc.fix_name_fields("Rahimova", "", "Madina ATT"), ("Madinaxon", "", "Rahimova ATT"))

    def test_middle_merged(self):
        self.assertEqual(gc.fix_name_fields("Madina", "", "Akbarova"), ("Madinaxon", "", "Akbarova"))

    def test_unchanged(self):
        self.assertIsNone(gc.fix_name_fields("Alişer", "", "Karimov"))

    def test_middle_kept_when_display_same(self):
        self.assertIsNone(gc.fix_name_fields("Alişer", "Rustam", "Karimov"))

    def test_empty(self):
        self.assertIsNone(gc.fix_name_fields("", "", ""))


class TestPerson(unittest.TestCase):
    def test_person(self):
        p = {"resourceName": "people/c1", "etag": "E1", "names": [{
            "metadata": {"primary": True}, "displayName": "Zilola Saidova DI",
            "givenName": "Zilola Saidova", "familyName": "DI", "unstructuredName": "x"}]}
        rn, etag, names, old, new = gc.fix_person(p)
        self.assertEqual((rn, etag), ("people/c1", "E1"))
        self.assertEqual(names, [{"givenName": "Zilolaxon", "familyName": "Saidova DI"}])
        self.assertEqual(new, "Zilolaxon Saidova DI")

    def test_no_names(self):
        self.assertIsNone(gc.fix_person({"resourceName": "people/c2", "etag": "E"}))


class TestCsv(unittest.TestCase):
    def test_csv(self):
        d = tempfile.mkdtemp()
        src = os.path.join(d, "c.csv")
        with open(src, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["First Name", "Middle Name", "Last Name", "File As", "Phone 1 - Value"])
            w.writerow(["Rahimova", "", "Madina ATT", "Rahimova Madina ATT", "+998000000001"])
            w.writerow(["Alişer", "", "Karimov", "", "+998000000002"])
        ch = gc.process_csv(src)
        self.assertEqual(len(ch), 1)
        rows = list(csv.DictReader(open(os.path.join(d, "c_tuzatilgan.csv"), encoding="utf-8-sig")))
        self.assertEqual((rows[0]["First Name"], rows[0]["Last Name"]), ("Madinaxon", "Rahimova ATT"))
        self.assertEqual(rows[0]["Phone 1 - Value"], "+998000000001")
        self.assertEqual(rows[1]["First Name"], "Alişer")


class TestToken(unittest.TestCase):
    def _files(self, cred_id, tok_id):
        import json
        d = tempfile.mkdtemp()
        c, t = os.path.join(d, "credentials.json"), os.path.join(d, "token.json")
        json.dump({"installed": {"client_id": cred_id}}, open(c, "w"))
        if tok_id is not None:
            json.dump({"client_id": tok_id}, open(t, "w"))
        return t, c

    def test_same_project(self):
        t, c = self._files("111-abc.apps.googleusercontent.com", "111-abc.apps.googleusercontent.com")
        self.assertTrue(gc.token_matches_credentials(t, c))

    def test_old_project_token(self):
        t, c = self._files("222-new.apps.googleusercontent.com", "111-old.apps.googleusercontent.com")
        self.assertFalse(gc.token_matches_credentials(t, c))

    def test_no_token(self):
        t, c = self._files("111-abc", None)
        self.assertFalse(gc.token_matches_credentials(t, c))


if __name__ == "__main__":
    unittest.main()
