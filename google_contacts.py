"""
Google Contacts (telefon kontaktlari) ismlarini names_logic.py qoidalari bilan tartibga soladi.

Ikki rejim:

  api  - Google People API orqali kontaktlarni JOYIDA yangilaydi (dublikat yaratmaydi).
         Birinchi marta ishga tushganda brauzerda Google'ga kirish so'raladi.
         python google_contacts.py api            # faqat ko'rsatadi (DRY_RUN)
         python google_contacts.py api --apply    # haqiqatan yangilaydi
         python google_contacts.py api --relogin  # eski akkaunt/loyihadan chiqib, qaytadan kirish

  csv  - contacts.google.com dan "Google CSV" qilib eksport qilingan faylni OFFLAYN tekshiradi
         va o'zgarishlar ro'yxatini (eski -> yangi) hamda tuzatilgan CSV'ni yozadi.
         python google_contacts.py csv contacts.csv
         DIQQAT: tuzatilgan CSV'ni Google'ga qayta import qilish dublikat yaratishi mumkin
         (Google import qilingan kontaktlarni mavjudlariga avtomatik almashtirmaydi).
         Yangilash uchun `api --apply` ni ishlating.

Sozlash (api rejimi uchun, bir marta):
  1. https://console.cloud.google.com -> yangi loyiha -> "People API" ni yoqing
  2. APIs & Services -> OAuth consent screen (External, o'zingizni test foydalanuvchi qilib qo'shing)
  3. Credentials -> Create OAuth client ID -> Desktop app -> JSON'ni `credentials.json` nomi bilan shu papkaga qo'ying
  pip install google-api-python-client google-auth-oauthlib
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime

import names_logic as nl

HERE = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS = os.path.join(HERE, "credentials.json")
TOKEN = os.path.join(HERE, "token.json")
BACKUP_DIR = os.path.join(HERE, "google_backups")
SCOPES = ["https://www.googleapis.com/auth/contacts"]
BATCH = 50                                   # People API: bir so'rovda 200 tagacha, biz ehtiyot uchun 50


def collapse(s):
    return re.sub(r"\s+", " ", s or "").strip()


# ---------------------------------------------------------------- umumiy mantiq
def fix_name_fields(given, middle, family):
    """
    (given, middle, family) -> yangi (given, middle, family) yoki None (o'zgarish yo'q).
    O'rta ism (middle) ism bilan birga ko'rib chiqiladi. Ko'rinadigan nom o'zgarmasa va
    o'rta ism bo'lsa, tuzilmaga tegilmaydi.
    """
    g, m, f = collapse(given), collapse(middle), collapse(family)
    first = collapse(f"{g} {m}")
    if not first and not f:
        return None
    nf, nlast, _ = nl.process_contact(first, f)
    same_display = collapse(f"{nf} {nlast}") == collapse(f"{first} {f}")
    if same_display and m:
        return None
    new = (nf, "", nlast)
    return None if new == (g, m, f) else new


# ---------------------------------------------------------------- CSV rejimi (offlayn)
CSV_LAYOUTS = [                              # (ism, o'rta, familiya, ko'rinadigan nom ustuni)
    ("First Name", "Middle Name", "Last Name", "File As"),
    ("Given Name", "Additional Name", "Family Name", "Name"),
]


def process_csv(src, dst=None):
    with open(src, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        layout = next((l for l in CSV_LAYOUTS if all(c in fields for c in l[:3])), None)
        if not layout:
            raise SystemExit("Google CSV ustunlari topilmadi (First Name / Last Name yoki Given Name / Family Name).")
        gcol, mcol, fcol, dcol = layout
        rows = list(reader)

    changes = []
    for r in rows:
        res = fix_name_fields(r.get(gcol), r.get(mcol), r.get(fcol))
        if not res:
            continue
        old_display = collapse(f"{r.get(gcol, '')} {r.get(mcol, '')} {r.get(fcol, '')}")
        new_display = collapse(f"{res[0]} {res[2]}")
        changes.append((old_display, new_display))
        r[gcol], r[mcol], r[fcol] = res
        if dcol in r and collapse(r[dcol]) == old_display:    # File As / Name ni ham yangilaymiz
            r[dcol] = new_display

    base = dst or os.path.splitext(src)[0] + "_tuzatilgan.csv"
    with open(base, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    prev = os.path.splitext(base)[0] + "_ozgarishlar.csv"
    with open(prev, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["eski", "yangi"])
        w.writerows(changes)
    print(f"{len(rows)} ta kontakt, {len(changes)} tasi o'zgaradi")
    print(f"  tuzatilgan CSV : {base}\n  o'zgarishlar   : {prev}")
    return changes


# ---------------------------------------------------------------- API rejimi
NAME_KEYS = ("givenName", "middleName", "familyName", "honorificPrefix", "honorificSuffix",
             "phoneticGivenName", "phoneticMiddleName", "phoneticFamilyName")


def fix_person(person):
    """People API 'person' dict -> (resourceName, etag, yangi_names, eski_nom, yangi_nom) yoki None."""
    names = person.get("names") or []
    if not names:
        return None
    idx = next((i for i, n in enumerate(names) if (n.get("metadata") or {}).get("primary")), 0)
    prim = names[idx]
    res = fix_name_fields(prim.get("givenName"), prim.get("middleName"), prim.get("familyName"))
    if not res:
        return None
    # faqat yoziladigan maydonlar (displayName, unstructuredName kabi chiqish maydonlari tashlanadi)
    new_names = []
    for i, n in enumerate(names):
        item = {k: n[k] for k in NAME_KEYS if n.get(k)}
        if i == idx:
            item.pop("middleName", None)
            for key, val in (("givenName", res[0]), ("familyName", res[2])):
                if val:
                    item[key] = val
                else:
                    item.pop(key, None)
        new_names.append(item)
    old = collapse(prim.get("displayName") or f"{prim.get('givenName', '')} {prim.get('familyName', '')}")
    new = collapse(f"{res[0]} {res[2]}")
    return person["resourceName"], person["etag"], new_names, old, new


def credentials_client_id(path=CREDENTIALS):
    """credentials.json ichidagi client_id (None: fayl yo'q yoki buzuq)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return (data.get("installed") or data.get("web") or {}).get("client_id")
    except (OSError, ValueError):
        return None


def token_matches_credentials(token_path=TOKEN, cred_path=CREDENTIALS):
    """token.json aynan shu credentials.json (shu loyiha) bilan olinganmi."""
    try:
        with open(token_path, encoding="utf-8") as f:
            tok_id = json.load(f).get("client_id")
    except (OSError, ValueError):
        return False
    return bool(tok_id) and tok_id == credentials_client_id(cred_path)


def get_service(relogin=False):
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        raise SystemExit("pip install google-api-python-client google-auth-oauthlib")
    if not os.path.exists(CREDENTIALS):
        raise SystemExit("credentials.json topilmadi (faylning boshidagi 'Sozlash' qismiga qarang).")

    client_id = credentials_client_id()
    if os.path.exists(TOKEN) and (relogin or not token_matches_credentials()):
        os.remove(TOKEN)                    # eski loyiha/akkauntdan qolgan token ishlatilmaydi
        print("Eski token.json o'chirildi, qayta kirish so'raladi.")
    # client_id ning boshidagi raqam = Google Cloud loyiha raqami
    print(f"Google Cloud loyiha raqami: {(client_id or '?').split('-')[0]}  "
          "(console.cloud.google.com dagi loyihangiz raqami bilan solishtiring)")

    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES) if os.path.exists(TOKEN) else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
            # select_account: brauzer akkauntni tanlashni so'raydi (eski akkauntga o'zi kirib ketmaydi)
            creds = flow.run_local_server(port=0, prompt="select_account consent")
        with open(TOKEN, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
    return build("people", "v1", credentials=creds)


def list_people(svc):
    people, token = [], None
    while True:
        r = svc.people().connections().list(
            resourceName="people/me", pageSize=1000, pageToken=token,
            personFields="names,metadata").execute()
        people += r.get("connections", [])
        token = r.get("nextPageToken")
        if not token:
            return people


def run_api(apply, relogin=False):
    svc = get_service(relogin)
    people = list_people(svc)
    print(f"Google kontaktlar: {len(people)} ta")

    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = os.path.join(BACKUP_DIR, f"google_contacts_{stamp}.json")
    with open(backup, "w", encoding="utf-8") as f:
        json.dump(people, f, ensure_ascii=False, indent=1)
    print(f"Zaxira: {os.path.relpath(backup, HERE)}")

    todo = [x for x in (fix_person(p) for p in people) if x]
    for _, _, _, old, new in todo:
        print(f"{old}  ->  {new}")
    print(f"\nO'zgaradi: {len(todo)} ta" + ("" if apply else "  (DRY_RUN - hech narsa o'zgarmadi; yozish uchun --apply)"))
    if not apply or not todo:
        return

    from googleapiclient.errors import HttpError
    done, problems = 0, []
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        body = {
            "contacts": {rn: {"etag": etag, "names": names} for rn, etag, names, _, _ in chunk},
            "updateMask": "names",
            "readMask": "names",
        }
        for attempt in (1, 2, 3):
            try:
                svc.people().batchUpdateContacts(body=body).execute()
                done += len(chunk)
                break
            except HttpError as e:
                if e.resp.status == 429 and attempt < 3:
                    print("Limit: 30s kutilmoqda ...")
                    time.sleep(30)
                    continue
                problems.append((str(e), [c[3] for c in chunk]))
                break
        time.sleep(1.5)
    print(f"Yangilandi: {done} ta")
    for err, olds in problems:
        print(f"XATO ({len(olds)} ta kontakt): {err}")


def main():
    ap = argparse.ArgumentParser(description="Google Contacts ismlarini tartibga solish")
    sub = ap.add_subparsers(dest="mode", required=True)
    a = sub.add_parser("api", help="People API orqali joyida yangilash")
    a.add_argument("--apply", action="store_true", help="haqiqatan yozadi (aks holda faqat ko'rsatadi)")
    a.add_argument("--relogin", action="store_true", help="eski kirishni o'chirib, akkauntni qaytadan tanlash")
    c = sub.add_parser("csv", help="Google CSV eksportini offlayn tekshirish")
    c.add_argument("file")
    c.add_argument("-o", "--out")
    args = ap.parse_args()
    if args.mode == "api":
        run_api(args.apply, args.relogin)
    else:
        process_csv(args.file, args.out)


if __name__ == "__main__":
    main()
