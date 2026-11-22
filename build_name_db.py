#!/usr/bin/env python3
"""
ismlar_hammasi_toliq.csv (ismlar_yigish.py natijasi) dan tozalangan
boy_names.json/csv va girl_names.json/csv bazalarini yasaydi.
rename_contacts.py shu fayllarni o'qiydi.

Tozalash:
  - sahifa raqamlari ("2", "10" ...) olib tashlanadi
  - "Burhon / Burxon", "Bodi, Bodiy", "Veja (Vija)" -> alohida ismlarga ajratiladi
  - lotin ichidagi kirill o'xshash harflar (Mаxsunbеk) lotinga o'giriladi
  - apostroflar bir xil qilinadi, takrorlar birlashtiriladi
  - mavjud boy_names.json / girl_names.json dagi ismlar saqlanadi

Ishlatish:
  python build_name_db.py                       # ismlar_hammasi_toliq.csv ni o'qiydi
  python build_name_db.py --csv boshqa.csv
"""
import argparse, csv, json, os, re

try:
    from transliterate import to_latin
except ImportError:                      # transliterate.py yonida bo'lmasa
    to_latin = None

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
APOS = "ʻʼ‘’`'´"
CYR = re.compile(r"[\u0400-\u04FF]")
LAT = re.compile(r"[A-Za-z]")
LOOKALIKE = {
    "а": "a", "А": "A", "с": "c", "С": "C", "е": "e", "Е": "E",
    "о": "o", "О": "O", "р": "p", "Р": "P", "х": "x", "Х": "X",
    "у": "y", "У": "Y", "к": "k", "К": "K", "В": "B", "Н": "H",
    "М": "M", "Т": "T", "і": "i", "І": "I", "ѕ": "s", "ј": "j",
}
APOS_TABLE = {ord(a): "'" for a in APOS}
BOY, GIRL = "O'g'il bola", "Qiz bola"


def key(name):
    """rename_contacts.name_key bilan bir xil bo'lishi SHART."""
    n = name.lower()
    for a in APOS:
        n = n.replace(a, "")
    n = n.replace("ö", "o").replace("ğ", "g").replace("ş", "sh").replace("ç", "ch")
    return n.replace("x", "h")


def variants(raw):
    s = (raw or "").strip()
    if CYR.search(s):
        if LAT.search(s):
            s = "".join(LOOKALIKE.get(c, c) for c in s)
        elif to_latin:
            s = to_latin(s)
    s = s.translate(APOS_TABLE)
    out = []
    for p in re.split(r"\s*(?:,|/|;|\(|\))\s*", s):
        p = p.strip(" -'")
        if not re.fullmatch(r"[A-Za-z'\-]{2,30}", p):     # raqam, bo'shliq, g'alati belgi
            continue
        if p.islower() or p.isupper():
            p = p.capitalize()
        out.append(p)
    return out


def load_json(path):
    path = os.path.join(DATA, path)
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="ismlar_hammasi_toliq.csv")
    args = ap.parse_args()

    db = {"boy": {}, "girl": {}}

    def add(gender, name, sources):
        k = key(name)
        if not k:
            return
        row = db[gender].setdefault(k, {"name": name, "normalized": k, "sources": set()})
        row["sources"] |= set(s for s in sources if s)

    # eski bazalar (qo'lda kiritilganlar ham saqlanadi)
    for g in ("boy", "girl"):
        for r in load_json(f"{g}_names.json"):
            for v in variants(r["name"]):
                add(g, v, r.get("source", "").split("|"))

    path = args.csv if os.path.isabs(args.csv) else os.path.join(DATA, args.csv)
    dropped = 0
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            g = "boy" if r["jins"].startswith("O'g") else "girl" if r["jins"].startswith("Qiz") else None
            if not g:
                continue
            vs = variants(r["ism"])
            if not vs:
                dropped += 1
            for v in vs:
                add(g, v, r.get("manba", "").split("; "))

    for g in ("boy", "girl"):
        out = sorted(
            ({"name": r["name"], "normalized": r["normalized"], "source": "|".join(sorted(r["sources"]))}
             for r in db[g].values()),
            key=lambda r: r["normalized"],
        )
        with open(os.path.join(DATA, f"{g}_names.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        with open(os.path.join(DATA, f"{g}_names.csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["name", "normalized", "source"])
            w.writeheader()
            w.writerows(out)
        print(f"{g}_names: {len(out)} ta ism")

    both = set(db["boy"]) & set(db["girl"])
    print(f"Ikkala ro'yxatda ham bor (xon qo'shilmaydi): {len(both)} ta")
    print(f"Tashlab yuborilgan (ism emas) qatorlar: {dropped}")


if __name__ == "__main__":
    main()
