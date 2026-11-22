"""
Telegram kontaktlarini tartibga soladi:
  - kirill -> lotin, o' g' sh ch -> ö ğ ş ç
  - ism-familiya almashgan yoki bitta maydonda bo'lsa -> ism | familiya (+ izoh)
  - qizlar ismiga "xon" qo'shadi

Sozlash (.env.example ga qarang):
  TG_API_ID, TG_API_HASH  (https://my.telegram.org -> API development tools)

Avval DRY_RUN = True (faqat ko'rsatadi), natijani ko'zdan kechirib, keyin DRY_RUN = False.
"""
import asyncio
import json
import os
from datetime import datetime

import names_logic as nl
from env_loader import load_env

DRY_RUN = True               # True = faqat ko'rsatadi, o'zgartirmaydi
HERE = os.path.dirname(os.path.abspath(__file__))


def credentials():
    load_env()                                   # .env fayli (bu skript yonida) o'qiladi
    api_id, api_hash = os.environ.get("TG_API_ID"), os.environ.get("TG_API_HASH")
    if not api_id or not api_hash:
        raise SystemExit("TG_API_ID va TG_API_HASH topilmadi. .env.example ni .env nomiga nusxalab, "
                         "qiymatlarni yozing (fayl rename_contacts.py bilan bir papkada bo'lsin).")
    if api_id == "123456" or api_hash == "your_api_hash":
        raise SystemExit(".env da namunaviy qiymatlar turibdi. my.telegram.org dagi haqiqiy API_ID/API_HASH ni yozing.")
    if not api_id.isdigit():
        raise SystemExit("TG_API_ID faqat raqamlardan iborat bo'lishi kerak.")
    return int(api_id), api_hash


def save_backups(users):
    """Zaxira HECH QACHON ustidan yozilmaydi: contacts_original.json (bir marta) + backups/<vaqt>.json."""
    backup = [{"id": u.id, "phone": u.phone, "first": u.first_name, "last": u.last_name} for u in users]
    os.makedirs(os.path.join(HERE, "backups"), exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    targets = [os.path.join(HERE, "backups", f"contacts_{stamp}.json")]
    original = os.path.join(HERE, "contacts_original.json")
    if not os.path.exists(original):
        targets.append(original)
    for path in targets:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(backup, f, ensure_ascii=False, indent=2)
    print(f"Zaxira saqlandi: {len(backup)} ta kontakt -> {', '.join(os.path.relpath(t, HERE) for t in targets)}")


async def main():
    from telethon import TelegramClient
    from telethon.tl.functions.contacts import GetContactsRequest, AddContactRequest
    from telethon.errors import FloodWaitError

    print(f"Ism bazasi: {len(nl.GIRL_KEYS)} ta qiz, {len(nl.BOY_KEYS)} ta o'g'il ismi")
    if len(nl.GIRL_KEYS) < 1000 or len(nl.BOY_KEYS) < 1000:
        print("DIQQAT: baza juda kichik. Avval `python build_name_db.py` ni ishga tushiring.")

    api_id, api_hash = credentials()
    async with TelegramClient(os.path.join(HERE, "userbot"), api_id, api_hash) as client:
        result = await client(GetContactsRequest(hash=0))
        save_backups(result.users)

        changed = 0
        problems = []          # (sabab, eski, yangi)
        expected = {}          # id -> (first, last, old, new)

        for u in result.users:
            first, last = u.first_name or "", u.last_name or ""
            old = f"{first} {last}".strip()
            if not old:
                problems.append(("Ismi bo'sh", old, ""))
                continue

            new_first, new_last, note = nl.process_contact(first, last)
            new = f"{new_first} {new_last}".strip()

            if nl.CYRILLIC.search(new):
                problems.append(("O'girilmagan kirill harf qoldi", old, new))
            if (new_first, new_last) == (first, last):
                continue

            print(f"{old}  ->  {new}"
                  + (f"   [{note}]" if note else "")
                  + ("" if u.phone else "   [raqamsiz]"))
            changed += 1
            expected[u.id] = (new_first, new_last, old, new)

            if not DRY_RUN:
                for attempt in (1, 2):          # FloodWait bo'lsa kutib, bir marta qayta uriniladi
                    try:
                        await client(AddContactRequest(
                            id=u, first_name=new_first, last_name=new_last,
                            phone=("+" + u.phone) if u.phone else "",
                            add_phone_privacy_exception=False))
                        await asyncio.sleep(1.5)
                        break
                    except FloodWaitError as e:
                        print(f"Kutish kerak: {e.seconds}s")
                        await asyncio.sleep(e.seconds + 1)
                        if attempt == 2:
                            problems.append(("Limit (FloodWait), qayta urining", old, new))
                    except Exception as e:
                        print(f"  XATO ({old}): {e}")
                        problems.append((f"Telegram xatosi: {e}", old, new))
                        break

        if not DRY_RUN and expected:
            await asyncio.sleep(2)
            fresh = await client(GetContactsRequest(hash=0))
            for u in fresh.users:
                if u.id in expected:
                    nf, nlast, old, new = expected[u.id]
                    if (u.first_name or "", u.last_name or "") != (nf, nlast):
                        if not any(p[1] == old for p in problems):
                            problems.append(("Yuborildi, lekin o'zgarmadi", old, new))

        print(f"\nJami o'zgargan: {changed}" + ("  (DRY_RUN - hech narsa o'zgarmadi)" if DRY_RUN else ""))
        print(f"O'zgarmay qolgan / muammoli: {len(problems)}")
        if problems:
            report = os.path.join(HERE, "problems_report.txt")
            with open(report, "w", encoding="utf-8") as f:
                for reason, old, new in problems:
                    line = f"[{reason}] {old}  ->  {new}"
                    print(line)
                    f.write(line + "\n")
            print("Ro'yxat problems_report.txt fayliga ham saqlandi")


if __name__ == "__main__":
    asyncio.run(main())
