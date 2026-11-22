import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import names_logic as nl


class TestProcess(unittest.TestCase):
    def check(self, first, last, exp_first, exp_last):
        f, l, _ = nl.process_contact(first, last)
        self.assertEqual((f, l), (exp_first, exp_last))

    # --- ism-familiya almashgan
    def test_swapped_girl_with_tag(self):
        self.check("Rahimova", "Madina ATT", "Madinaxon", "Rahimova ATT")

    def test_swapped_girl_unknown_name_in_one_field(self):
        self.check("Saidova Sevinbika", "", "Sevinbikaxon", "Saidova")

    def test_swapped_boy(self):
        self.check("Karimov", "Alisher", "Alişer", "Karimov")

    # --- bazada yo'q ism, familiya bo'yicha jins
    def test_unknown_girl_by_surname(self):
        self.check("Zorinta", "Yusupova ATT", "Zorintaxon", "Yusupova ATT")

    def test_unknown_boy_by_surname(self):
        self.check("Zzxqname", "Tojidinov ATT", "Zzxqname", "Tojidinov ATT")

    # --- bitta maydonda
    def test_full_name_in_first(self):
        self.check("Zilola Saidova", "DI", "Zilolaxon", "Saidova DI")

    def test_name_title_tag(self):
        self.check("Malika Ustoz", "Ofis", "Malikaxon", "Ustoz Ofis")

    def test_boy_full_name_unchanged(self):
        self.check("Ali Valiyev", "", "Ali", "Valiyev")

    # --- xon qo'shilmasligi kerak bo'lganlar
    def test_boys_ending_with_a(self):
        for n in ("Hamza", "Abdulla", "Zakariya", "Nodir", "Temur"):
            self.check(n, "", n, "")

    def test_idempotent(self):
        f, l, _ = nl.process_contact("Rahimova", "Madina ATT")
        self.assertEqual(nl.process_contact(f, l)[:2], (f, l))

    def test_already_xon(self):
        self.check("Nigoraxon", "", "Nigoraxon", "")

    def test_titles_untouched(self):
        for n in ("Ustoz", "Opa", "Mama"):
            self.check(n, "", n, "")

    # --- umumiy holatlar
    def test_tag_between(self):
        self.check("Ali ATT Karimov", "", "Ali", "Karimov ATT")

    def test_patronymic_boy(self):
        self.check("Karimov Alisher Rustam o'g'li", "", "Alişer", "Karimov Rustam öğli")

    def test_patronymic_girl(self):
        self.check("Aliyeva Zilola Bahodir qizi", "", "Zilolaxon", "Aliyeva Bahodir qizi")

    def test_lowercase(self):
        self.check("madina akbarova", "", "Madinaxon", "Akbarova")

    def test_uppercase(self):
        self.check("DILNOZA KARIMOVA", "", "Dilnozaxon", "Karimova")

    def test_leading_title_keeps_order(self):
        self.check("Ustoz Dilnoza Karimova", "", "Ustoz Dilnozaxon Karimova", "")
        self.check("Ustoz", "Dilnoza Karimova", "Ustoz", "Dilnozaxon Karimova")

    def test_title_before_name_no_surname(self):
        self.check("Opa Dilnoza", "", "Opa Dilnozaxon", "")

    def test_empty_first_field(self):
        self.check("", "Madina Akbarova", "Madinaxon", "Akbarova")

    def test_ambiguous_left_alone(self):
        self.check("Madina Dilnoza Akbarova", "", "Madina Dilnoza Akbarova", "")
        self.check("Mahalla Raisi Karimov", "", "Mahalla Raisi Karimov", "")

    def test_emoji_kept(self):
        self.check("Madina Akbarova \U0001F4DE", "", "Madinaxon", "Akbarova \U0001F4DE")

    # --- ism bo'lmagan so'zlar ("a" bilan tugasa ham) xon olmasligi kerak
    def test_not_names_ending_with_a(self):
        self.check("Usluga", "DJ", "Usluga", "DJ")
        self.check("Golosovaya pochta", "", "Golosovaya poçta", "")
        self.check("Svoya melodiya", "", "Svoya melodiya", "")
        self.check("Zorinta", "Admin", "Zorinta", "Admin")
        self.check("Pochta", "Aloqa", "Poçta", "Aloqa")
        self.check("Melitsiya", "", "Melitsiya", "")

    def test_extra_file(self):
        import tempfile
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "x.txt"), "w", encoding="utf-8") as f:
            f.write("# izoh\nZorinta\nSevin'bika  # sharh\n")
        self.assertEqual(nl.load_extra("x.txt", d), {nl.name_key("Zorinta"), nl.name_key("Sevin'bika")})

    def test_extra_overrides_ambiguous(self):
        k = nl.name_key("Bahor")                      # bazada ikkala jinsda ham bor
        self.assertEqual(nl.db_gender("Bahor"), "u")
        nl.EXTRA_GIRL_KEYS.add(k)
        try:
            self.assertEqual(nl.db_gender("Bahor"), "f")
            nl.EXTRA_BOY_KEYS.add(k)                  # ikkala faylda bo'lsa - yana noaniq
            self.assertEqual(nl.db_gender("Bahor"), "u")
        finally:
            nl.EXTRA_GIRL_KEYS.discard(k)
            nl.EXTRA_BOY_KEYS.discard(k)

    # --- kirill
    def test_cyrillic(self):
        f, l, _ = nl.process_contact("Мадина", "Акбарова")
        self.assertEqual((f, l), ("Madinaxon", "Akbarova"))


if __name__ == "__main__":
    unittest.main()
