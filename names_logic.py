"""
Kontakt ismlarini tartibga solish mantig'i (Telegram'ga bog'liq emas, shuning uchun test qilish oson).

  convert(text)                 kirill -> lotin, o' g' sh ch -> ö ğ ş ç
  process_contact(first, last)  (yangi_ism, yangi_familiya, izoh) qaytaradi
"""
import json
import os
import re

from transliterate import to_latin, CYRILLIC_TO_LATIN

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")

# ---------------------------------------------------------------- sozlamalar
ADD_XON = True               # qizlar ismiga "xon" qo'shish
SWAP_NAMES = True            # familiya ism o'rnida yozilgan bo'lsa, o'rnini almashtirish
NORMALIZE_STRUCTURE = True   # "Madina Akbarova" / "Akbarova Madina ATT" -> ism | familiya + izoh
FIX_CASE = True             # madina -> Madina, DILNOZA -> Dilnoza
SPLIT_FIELDS = True          # False: ko'rinadigan nom o'zgarmasa (faqat maydon chegarasi o'zgarsa), kontakt yozilmaydi

APOS = "ʻʼ‘’`'´"
CYRILLIC = re.compile(r"[\u0400-\u052F\u1C80-\u1C8F\u2DE0-\u2DFF\uA640-\uA69F]")
LATIN = re.compile(r"[A-Za-z]")
WORD = re.compile(rf"[^\W\d_]+(?:[{APOS}][^\W\d_]+)*")


# ---------------------------------------------------------------- kirill -> lotin
def special_letters(text: str) -> str:
    def og(m):
        return {"o": "ö", "O": "Ö", "g": "ğ", "G": "Ğ"}[m.group(1)]
    text = re.sub(rf"([oOgG])[{APOS}]", og, text)

    def shch(m):
        s = m.group(0)
        r = "ş" if s.lower() == "sh" else "ç"
        return r.upper() if s[0].isupper() else r
    return re.sub(r"(?i)sh|ch", shch, text)


LOOKALIKE = {
    "а": "a", "А": "A", "с": "c", "С": "C", "е": "e", "Е": "E",
    "о": "o", "О": "O", "р": "p", "Р": "P", "х": "x", "Х": "X",
    "у": "y", "У": "Y", "к": "k", "К": "K", "В": "B", "Н": "H",
    "М": "M", "Т": "T", "і": "i", "І": "I", "ѕ": "s", "ј": "j",
}


def convert_word(word: str) -> str:
    if not CYRILLIC.search(word):
        return word
    if LATIN.search(word):               # lotin + kirill aralash
        out = []
        for ch in word:
            if ch in LOOKALIKE:
                out.append(LOOKALIKE[ch])
            elif ch in CYRILLIC_TO_LATIN:
                out.append(CYRILLIC_TO_LATIN[ch])
            else:
                out.append(ch)
        return "".join(out)
    return to_latin(word).replace("ʼ", "")


def convert(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"\S+", lambda m: convert_word(m.group(0)), text)
    return special_letters(text)


# ---------------------------------------------------------------- ism bazasi
def name_key(name: str) -> str:
    """Solishtirish kaliti (build_name_db.key bilan bir xil): ö->o, ş->sh, x->h, apostrofsiz."""
    n = name.lower()
    for a in APOS:
        n = n.replace(a, "")
    n = n.replace("ö", "o").replace("ğ", "g").replace("ş", "sh").replace("ç", "ch")
    return n.replace("x", "h")


SURNAME_END = ("yeva", "eva", "ova", "ovna", "evna", "yev", "ev", "ov", "qizi", "ogli", "uli")
FEMALE_SURNAME_END = ("yeva", "eva", "ova", "ovna", "evna", "qizi")
MALE_SURNAME_END = ("ev", "ov", "ogli", "uli")
MALE_MARK = ("boy", "bay", "bek", "hoja", "iddin", "uddin", "ullo", "ulla", "mirzo", "mirza")
MALE_A = {"hamza", "abdulla", "dima", "misha", "sasha", "kolya", "vasya",
          "petya", "tolya", "vanya", "slava", "nikita", "ilya", "danila", "luka"}
# ism EMAS: qarindosh / lavozim / unvon so'zlari
NOT_NAMES = {"ona", "opa", "aya", "mama", "dada", "buvi", "buva", "xola",
             "amma", "kelin", "oyi", "ustoz", "mijoz", "taxi", "doktor",
             "acha", "ammacha", "ammajon", "ammaxol", "ammaqiz", "opajon",
             "domla", "muallima", "direktor", "aka", "uka", "akam", "ukam",
             "singil", "singlim", "dugona", "qoshni", "tog'a", "togam"}
# bazada bo'lmasa ham qiz ismi deb hisoblanadigan (qo'lda to'ldiring; kalit: apostrof/ö/ş siz kichik harf)
FEMALE_EXTRA = {"gulnoz", "dilnoz", "nigor", "shirin", "zilola", "gulchehra",
                "mehriniso", "oydin", "zebo", "nilufar", "munisa"}
ALREADY_XON = ("xon", "xan", "hon")

NOT_KEYS = {name_key(x) for x in NOT_NAMES}
MALE_A_KEYS = {name_key(x) for x in MALE_A}
FEMALE_EXTRA_KEYS = {name_key(x) for x in FEMALE_EXTRA}


def load_names(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"Diqqat: {path} topilmadi (python build_name_db.py ni ishga tushiring)")
        return set()
    with open(path, encoding="utf-8") as f:
        return {name_key(r["name"]) for r in json.load(f)} - NOT_KEYS


def load_extra(filename, directory=DATA_DIR):
    """Matn fayli: har qatorda bitta ism, '#' dan keyin izoh. Fayl bo'lmasa bo'sh to'plam."""
    path = os.path.join(directory, filename)
    keys = set()
    if os.path.exists(path):
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.split("#", 1)[0].strip()
                if line:
                    keys.add(name_key(line))
    return keys


NOT_KEYS |= load_extra("extra_not_names.txt")          # ism emas (data/extra_not_names.txt)
GIRL_KEYS = (load_names("girl_names.json") | load_extra("extra_girl_names.txt")) - NOT_KEYS
BOY_KEYS = (load_names("boy_names.json") | load_extra("extra_boy_names.txt")) - NOT_KEYS


# ---------------------------------------------------------------- yordamchi funksiyalar
def is_surname(word: str) -> bool:
    k = name_key(word)
    return any(k.endswith(e) and len(k) >= len(e) + 3 for e in SURNAME_END)


def is_male_surname(word: str) -> bool:
    return is_surname(word) and name_key(word).endswith(MALE_SURNAME_END)


def is_female_surname(word: str) -> bool:
    return is_surname(word) and name_key(word).endswith(FEMALE_SURNAME_END)


def is_tag(tok: str) -> bool:
    """Ism ham, familiya ham emas: ATT, DI, 16-Maktab, Ustoz, emoji ..."""
    k = name_key(tok)
    if not WORD.fullmatch(tok) or k in NOT_KEYS:
        return True
    return tok.isupper() and len(tok) <= 3 and k not in GIRL_KEYS and k not in BOY_KEYS


def db_gender(name: str):
    """'f' / 'm' / 'u' (ikkala ro'yxatda) / None (bazada yo'q). 'xon' qo'shilgan shaklni ham taniydi."""
    k = name_key(name)
    for kk in (k, k[:-3] if k.endswith("hon") else None):
        if not kk:
            continue
        g, b = kk in GIRL_KEYS, kk in BOY_KEYS
        if g and b:
            return "u"
        if g:
            return "f"
        if b:
            return "m"
    return None


def gender_of(name: str, surname: str = None):
    """Ustuvorlik: bazadagi aniq jins -> familiya qo'shimchasi -> ism oxiri (taxmin)."""
    g = db_gender(name)
    if g in ("f", "m"):
        return g
    if surname:
        if is_female_surname(surname):
            return "f"
        if is_male_surname(surname):
            return "m"
    if g == "u":
        return None
    k = name_key(name)
    if k in MALE_A_KEYS or k.endswith(MALE_MARK):
        return "m"
    # bazada ham, familiya qo'shimchasida ham dalil bo'lmasa - TAXMIN QILINMAYDI (faqat qo'lda kiritilganlar)
    return "f" if k in FEMALE_EXTRA_KEYS else None


def with_xon(name: str) -> str:
    if not WORD.fullmatch(name) or name.lower().endswith(ALREADY_XON):
        return name
    return name + ("XON" if name.isupper() else "xon")


# ---------------------------------------------------------------- asosiy mantiq
def fix_case(tok: str) -> str:
    """madina -> Madina, DILNOZA -> Dilnoza (ATT, DI kabi qisqa izohlarga tegmaydi)."""
    if not FIX_CASE or not WORD.fullmatch(tok):
        return tok
    if tok.islower():
        return tok[0].upper() + tok[1:]
    if tok.isupper() and len(tok) >= 4:
        return tok[0] + tok[1:].lower()
    return tok


def _plain(tok: str) -> bool:
    return not is_tag(tok) and not is_surname(tok)


def find_pair(tokens):
    """Familiya (s) va uning yonidagi ism (m) indekslari. Orada faqat izohlar (ATT, DI ...) bo'lishi mumkin."""
    s = next((i for i, t in enumerate(tokens) if not is_tag(t) and is_surname(t)), None)
    if s is None:
        return None, None
    left = next((i for i in range(s - 1, -1, -1) if not is_tag(tokens[i])), None)
    if left is not None and _plain(tokens[left]):
        return s, left
    right = next((i for i in range(s + 1, len(tokens)) if not is_tag(tokens[i])), None)
    if right is not None and _plain(tokens[right]):
        return s, right
    return s, None


def normalize_person(first: str, last: str):
    """
    Ism va familiya almashgan / bitta maydonda / izoh bilan aralash bo'lsa tartibga soladi:
        ("Rahimova", "Madina ATT")              -> ("Madinaxon", "Rahimova ATT")
        ("Zilola Saidova", "DI")              -> ("Zilolaxon", "Saidova DI")
        ("Saidova Sevinbika", "")             -> ("Sevinbikaxon", "Saidova")
        ("Karimov Alisher Rustam o'g'li", "")    -> ("Alisher", "Karimov Rustam o'g'li")
        ("Ustoz Dilnoza Karimova", "")           -> ("Ustoz Dilnozaxon Karimova", "")   [tartib saqlanadi]
        ("madina akbarova", "")                  -> ("Madinaxon", "Akbarova")
    Odam ismi ekanligiga ishonch bo'lmasa None qaytaradi.
    Qaytaradi: (ism, familiya, almashtirildi_mi)
    """
    tokens = f"{first} {last}".split()
    if len(tokens) < 2:
        return None
    n_first = len(first.split())

    s, m = find_pair(tokens)
    if s is not None:
        if m is None:
            return None
    else:
        m = next((i for i, t in enumerate(tokens) if not is_tag(t)), None)
        if m is None or db_gender(tokens[m]) is None:
            return None

    lead = tokens[:min(m, s if s is not None else m)]       # ism/familiyadan oldingi so'zlar
    if any(not is_tag(t) for t in lead):                    # "Madina Dilnoza Akbarova" - noaniq
        return None
    swapped = s is not None and s < m
    if swapped and (not SWAP_NAMES or len(tokens[m]) < 3):
        return None

    surname = fix_case(tokens[s]) if s is not None else None
    name = fix_case(tokens[m])
    if ADD_XON and gender_of(name, surname) == "f":
        name = with_xon(name)

    if lead:                                                # oldida unvon bor: tartibni o'zgartirmaymiz
        out = list(tokens)
        out[m] = name
        if s is not None:
            out[s] = surname
        return " ".join(out[:n_first]), " ".join(out[n_first:]), False

    rest = [t for i, t in enumerate(tokens) if i not in (m, s)]
    return name, " ".join(([surname] if surname else []) + rest), swapped


# eski (bitta so'zli) mantiq: normalize_person ishonch bilan hal qila olmagan holatlar uchun
def looks_female(first: str, last: str = "") -> bool:
    k = name_key(first)
    if k in NOT_KEYS or k in MALE_A_KEYS:
        return False
    if is_surname(first) or k.endswith(MALE_MARK):
        return False
    if k in BOY_KEYS:
        return False
    if k in GIRL_KEYS:
        return True
    if last and is_male_surname(last):
        return False
    return k in FEMALE_EXTRA_KEYS            # bazada yo'q so'zni "a" bilan tugagani uchun qiz ismi deb olmaymiz


def add_xon(first: str, last: str) -> str:
    if not first or not WORD.fullmatch(first):
        return first
    if first.lower().endswith(ALREADY_XON):
        return first
    return with_xon(first) if looks_female(first, last) else first


def is_boy_name(word: str) -> bool:
    k = name_key(word)
    return k in BOY_KEYS and k not in GIRL_KEYS


def should_swap(first: str, last: str) -> bool:
    if not (first and last and WORD.fullmatch(first) and WORD.fullmatch(last)):
        return False
    kf, kl = name_key(first), name_key(last)
    if kf in GIRL_KEYS or kf in BOY_KEYS or kf.endswith(MALE_MARK) or is_surname(last):
        return False
    if is_boy_name(last):
        return is_surname(first)
    if not looks_female(last):
        return False
    return is_surname(first) or kl in GIRL_KEYS


def process_contact(first: str, last: str):
    """(yangi_ism, yangi_familiya, izoh) - izoh: '', 'almashtirildi' yoki 'tartibga solindi'."""
    first, last = convert(first or ""), convert(last or "")
    if NORMALIZE_STRUCTURE:
        res = normalize_person(first, last)
        if res:
            nf, nl, swapped = res
            if not SPLIT_FIELDS and f"{nf} {nl}".strip() == f"{first} {last}".strip():
                return first, last, ""
            return nf, nl, ("almashtirildi" if swapped else "")
    swapped = False
    if SWAP_NAMES and should_swap(first, last):
        first, last = last, first
        swapped = True
    if ADD_XON:
        first = add_xon(first, last)
    return first, last, ("almashtirildi" if swapped else "")
