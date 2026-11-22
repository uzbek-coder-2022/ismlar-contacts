"""
Kontaktlarni zaxira faylidagi asl holatiga qaytaradi.

Ishlatish:
  python restore_contacts.py                       # contacts_original.json (DRY_RUN: faqat ko'rsatadi)
  python restore_contacts.py backups/contacts_20250101_120000.json
DRY_RUN = False qilganda haqiqatan qaytaradi.
"""
import asyncio, json, os, sys

DRY_RUN = True

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "contacts_original.json")


async def main():
    from telethon import TelegramClient
    from telethon.tl.functions.contacts import GetContactsRequest, AddContactRequest
    from telethon.errors import FloodWaitError
    from rename_contacts import credentials
    api_id, api_hash = credentials()
    with open(SRC, encoding="utf-8") as f:
        saved = {r["id"]: r for r in json.load(f)}
    print(f"Zaxira: {SRC} ({len(saved)} ta kontakt)")

    async with TelegramClient(os.path.join(HERE, "userbot"), api_id, api_hash) as client:
        users = (await client(GetContactsRequest(hash=0))).users
        restored = 0
        for u in users:
            r = saved.get(u.id)
            if not r:
                continue
            if (u.first_name or "", u.last_name or "") == (r["first"] or "", r["last"] or ""):
                continue
            print(f"{u.first_name or ''} {u.last_name or ''}  ->  {r['first'] or ''} {r['last'] or ''}")
            restored += 1
            if not DRY_RUN:
                try:
                    await client(AddContactRequest(
                        id=u, first_name=r["first"] or "", last_name=r["last"] or "",
                        phone=("+" + u.phone) if u.phone else "",
                        add_phone_privacy_exception=False))
                    await asyncio.sleep(1.5)
                except FloodWaitError as e:
                    print(f"Kutish kerak: {e.seconds}s")
                    await asyncio.sleep(e.seconds + 1)
                except Exception as e:
                    print(f"  XATO: {e}")
        print(f"Qaytariladigan: {restored}" + ("  (DRY_RUN - hech narsa o'zgarmadi)" if DRY_RUN else ""))

if __name__ == "__main__":
    asyncio.run(main())
