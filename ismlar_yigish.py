#!/usr/bin/env python3
"""
O'zbekcha ismlar (o'g'il va qiz bolalar) ro'yxatini saytlardan yig'ib, CSV qiladi.

Manbalar:
  bilmaysizmi.uz  - ism + ma'no + kelib chiqishi (sahifalab o'tadi)
  ismlar.com      - faqat ismlar (har bir harf, har bir sahifa)

O'rnatish:
  pip install requests beautifulsoup4

Ishlatish:
  python ismlar_yigish.py
  python ismlar_yigish.py --merge data/ismlar_hammasi_toliq.csv
  python ismlar_yigish.py --sources bilmaysizmi          # faqat bitta manba
  python ismlar_yigish.py --delay 1.5                    # sekinroq (saytga yengil)

Natija: ismlar_hammasi.csv (UTF-8, Excel'da ochiladi)
Ustunlar: ism, jins, manosi, kelib_chiqishi, manba
"""
import argparse
import csv
import re
import sys
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BOY = "O'g'il bola"
GIRL = "Qiz bola"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "uz,en;q=0.8",
}

APOS = str.maketrans({"\u2018": "'", "\u2019": "'", "\u02bb": "'", "\u02bc": "'", "`": "'", "\u00b4": "'"})

session = requests.Session()
session.headers.update(HEADERS)
DELAY = 0.7


def clean(s):
    return re.sub(r"\s+", " ", (s or "").translate(APOS)).strip()


def norm_key(name):
    return clean(name).lower()


class FetchError(Exception):
    """Sahifa bir necha urinishdan keyin ham yuklanmadi (404 emas)."""


FAILED = []      # yuklanmagan sahifalar (oxirida ko'rsatiladi)


def get(url, retries=5):
    """Matn qaytaradi; 404 bo'lsa None (sahifalar tugadi); boshqa xatoda FetchError."""
    for i in range(retries):
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 200:
                time.sleep(DELAY)
                return r.text
            if r.status_code == 404:
                return None
            print(f"  ! {r.status_code}: {url}", file=sys.stderr)
        except requests.RequestException as e:
            print(f"  ! xato ({e.__class__.__name__}): {url}", file=sys.stderr)
        time.sleep(3 * (i + 1))
    FAILED.append(url)
    raise FetchError(url)


# ---------------------------------------------------------------- bilmaysizmi.uz
BM_BASE = "https://bilmaysizmi.uz"
BM_LISTS = [
    (BM_BASE + "/ismlar/ogil-bolalar-ismi", BOY),
    (BM_BASE + "/ismlar/qiz-bolalar-ismi", GIRL),
]


def _find_card(link):
    """'Ko'rish ->' havolasidan boshlab, ism havolasini ham o'z ichiga olgan eng kichik konteynerni topadi."""
    href = link["href"]
    node = link
    for _ in range(6):
        node = node.parent
        if node is None:
            return None, None
        for a in node.find_all("a", href=True):
            if a["href"] == href and "\u2192" not in a.get_text():
                return node, a
    return None, None


def parse_bilmaysizmi(html, gender):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for link in soup.find_all("a", href=True):
        if "\u2192" not in link.get_text():  # "Ko'rish →"
            continue
        card, name_a = _find_card(link)
        if card is None:
            continue
        name = clean(name_a.get_text())
        origins = [
            clean(x.get_text())
            for x in card.find_all("a", href=True)
            if "/kelib-chiqishi/" in x["href"]
        ]
        paras = [clean(p.get_text()) for p in card.find_all("p")]
        meaning = max(paras, key=len) if paras else ""
        if name:
            out.append(
                {
                    "ism": name,
                    "jins": gender,
                    "manosi": meaning,
                    "kelib_chiqishi": ", ".join(origins),
                    "manba": "bilmaysizmi.uz",
                    "_id": urljoin(BM_BASE, link["href"]),
                }
            )
    return out


def scrape_bilmaysizmi():
    results = []
    for base, gender in BM_LISTS:
        print(f"[bilmaysizmi.uz] {gender}")
        seen = set()
        page = 1
        fails = 0
        while page <= 300:
            url = base if page == 1 else f"{base}?page={page}"
            try:
                html = get(url)
            except FetchError:
                fails += 1
                if fails >= 3:
                    break
                page += 1
                continue
            fails = 0
            if not html:
                break
            items = parse_bilmaysizmi(html, gender)
            new = [it for it in items if it["_id"] not in seen]
            print(f"  sahifa {page}: {len(items)} ta, yangi: {len(new)}")
            if not new:
                break
            for it in new:
                seen.add(it["_id"])
                results.append(it)
            page += 1
    return results


# ---------------------------------------------------------------- ismlar.com
IS_BASE = "https://ismlar.com"
FALLBACK_LETTERS = (
    ["A", "B", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "X", "Y", "Z"]
    + ["O\u2018", "G\u2018", "Sh", "Ch"]
)


def ismlar_letter_urls(gender_key):
    try:
        html = get(f"{IS_BASE}/names/{gender_key}")
    except FetchError:
        html = None
    urls = []
    if html:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            h = urljoin(IS_BASE, a["href"]).split("?")[0]
            if f"/letter/{gender_key}/" in h and h not in urls:
                urls.append(h)
    if not urls:
        from urllib.parse import quote

        urls = [f"{IS_BASE}/letter/{gender_key}/{quote(l)}" for l in FALLBACK_LETTERS]
    return urls


def parse_ismlar(html, gender):
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for a in soup.find_all("a", href=True):
        h = urljoin(IS_BASE, a["href"])
        if "/name/" in h and "/favourite/" not in h:
            name = clean(a.get_text())
            if name:
                out.append(
                    {
                        "ism": name,
                        "jins": gender,
                        "manosi": "",
                        "kelib_chiqishi": "",
                        "manba": "ismlar.com",
                        "_id": h,
                    }
                )
    return out


def scrape_ismlar():
    results = []
    for gender_key, gender in (("boy", BOY), ("girl", GIRL)):
        letters = ismlar_letter_urls(gender_key)
        print(f"[ismlar.com] {gender}: {len(letters)} ta harf")
        for lurl in letters:
            seen = set()
            page = 1
            fails = 0
            while page <= 300:
                url = lurl if page == 1 else f"{lurl}?page={page}"
                try:
                    html = get(url)
                except FetchError:
                    fails += 1
                    if fails >= 3:
                        break
                    page += 1
                    continue
                fails = 0
                if not html:
                    break
                items = parse_ismlar(html, gender)
                new = [it for it in items if it["_id"] not in seen]
                if not new:
                    break
                for it in new:
                    seen.add(it["_id"])
                    results.append(it)
                page += 1
            print(f"  {lurl.rsplit('/', 1)[-1]}: {len(seen)} ta (sahifa: {page - 1})")
    return results


# ---------------------------------------------------------------- birlashtirish
def load_existing(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append(
                {
                    "ism": clean(r.get("ism")),
                    "jins": r.get("jins", ""),
                    "manosi": r.get("manosi", ""),
                    "kelib_chiqishi": r.get("kelib_chiqishi", ""),
                    "manba": r.get("manba", ""),
                }
            )
    return rows


def merge(rows):
    """Bir xil (ism, jins) takrorlansa: ma'nosi bor yozuv ustun; manbalar birlashtiriladi."""
    merged = {}
    for r in rows:
        k = (norm_key(r["ism"]), r["jins"])
        if k not in merged:
            merged[k] = dict(r)
            continue
        cur = merged[k]
        if not cur["manosi"] and r["manosi"]:
            cur["manosi"] = r["manosi"]
        if not cur["kelib_chiqishi"] and r["kelib_chiqishi"]:
            cur["kelib_chiqishi"] = r["kelib_chiqishi"]
        srcs = set(cur["manba"].split("; ")) | set(r["manba"].split("; "))
        cur["manba"] = "; ".join(sorted(s for s in srcs if s))
    return sorted(merged.values(), key=lambda r: (r["jins"], norm_key(r["ism"])))


def main():
    global DELAY
    ap = argparse.ArgumentParser(description="Ismlar ro'yxatini yig'ish")
    ap.add_argument("--sources", nargs="+", default=["bilmaysizmi", "ismlar"], choices=["bilmaysizmi", "ismlar"])
    ap.add_argument("--merge", help="Mavjud CSV (masalan, ismlar.csv) bilan birlashtirish")
    ap.add_argument("--out", default="data/ismlar_hammasi_toliq.csv")
    ap.add_argument("--delay", type=float, default=0.7, help="so'rovlar orasidagi kutish (soniya)")
    args = ap.parse_args()
    DELAY = args.delay

    rows = []
    if args.merge:
        rows += load_existing(args.merge)
        print(f"Mavjud fayldan: {len(rows)} ta")

    try:
        if "bilmaysizmi" in args.sources:
            rows += scrape_bilmaysizmi()
        if "ismlar" in args.sources:
            rows += scrape_ismlar()
    except KeyboardInterrupt:
        print("\nTo'xtatildi. Hozirgacha yig'ilganlar saqlanadi.")

    if FAILED:
        with open("yuklanmagan_sahifalar.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(FAILED))
        print(f"\nDIQQAT: {len(FAILED)} ta sahifa yuklanmadi (yuklanmagan_sahifalar.txt). "
              "Skriptni --merge bilan qayta ishga tushiring, yetishmaganlari to'ldiriladi.")

    final = merge(rows)
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["ism", "jins", "manosi", "kelib_chiqishi", "manba"], extrasaction="ignore")
        w.writeheader()
        w.writerows(final)

    boys = sum(1 for r in final if r["jins"] == BOY)
    girls = sum(1 for r in final if r["jins"] == GIRL)
    print(f"\nTayyor: {args.out}  |  jami {len(final)} (o'g'il: {boys}, qiz: {girls})")


if __name__ == "__main__":
    main()
