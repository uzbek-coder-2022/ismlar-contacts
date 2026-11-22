import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from env_loader import load_env


class TestEnv(unittest.TestCase):
    def test_load(self):
        for k in ("T_A", "T_B", "T_C", "T_D"):
            os.environ.pop(k, None)
        d = tempfile.mkdtemp()
        p = os.path.join(d, ".env")
        with open(p, "w", encoding="utf-8-sig") as f:
            f.write("# izoh\nT_A=111\nexport T_B = \"abc def\"\nT_C='x'  \nT_D=hash123 # sharh\n\nbuzuq qator\n")
        os.environ["T_C"] = "tizim"                     # tizim qiymati ustun
        self.assertTrue(load_env(p))
        self.assertEqual(os.environ["T_A"], "111")
        self.assertEqual(os.environ["T_B"], "abc def")
        self.assertEqual(os.environ["T_C"], "tizim")
        self.assertEqual(os.environ["T_D"], "hash123")

    def test_missing(self):
        self.assertFalse(load_env(os.path.join(tempfile.mkdtemp(), ".env")))


if __name__ == "__main__":
    unittest.main()
