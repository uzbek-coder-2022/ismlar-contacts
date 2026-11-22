# ismlar-contacts

O'zbekcha ismlar bazasini (o'g'il va qiz bolalar) yig'ish va Telegram kontaktlarini tartibga solish:

- kirill -> lotin, `o'`, `g'`, `sh`, `ch` -> `ö`, `ğ`, `ş`, `ç`
- ism va familiya almashib qolgan bo'lsa tuzatish (`Rahimova | Madina ATT` -> `Madinaxon | Rahimova ATT`)
- ism va familiya bitta maydonda bo'lsa ajratish (`Zilola Saidova | DI` -> `Zilolaxon | Saidova DI`)
- qizlar ismiga `xon` qo'shish (yigitlar uchun ham ism-familiya tartibi to'g'rilanadi)

Jinsni aniqlash tartibi: ism bazasi -> familiya qo'shimchasi (`-ova/-eva` = qiz, `-ov/-ev` = yigit).
Bazada yo'q va familiya ham dalil bermasa, "xon" **qo'shilmaydi** (ism oxiriga qarab taxmin qilinmaydi,
shuning uchun `Usluga`, `Pochta`, `Melodiya` kabi so'zlar o'zgarmaydi).

Bazada yo'q ismlarni `data/extra_girl_names.txt` / `data/extra_boy_names.txt` ga (har qatorda bittadan),
ism bo'lmagan so'zlarni `data/extra_not_names.txt` ga yozing - kodni tahrirlash shart emas.

## Qo'llab-quvvatlanadigan holatlar
| Kontakt (ism / familiya) | Natija |
|---|---|
| `Rahimova` / `Madina ATT` | `Madinaxon` / `Rahimova ATT` |
| `Zilola Saidova` / `DI` | `Zilolaxon` / `Saidova DI` |
| `Karimov Alisher Rustam o'g'li` | `Alişer` / `Karimov Rustam öğli` |
| `Aliyeva Zilola Bahodir qizi` | `Zilolaxon` / `Aliyeva Bahodir qizi` |
| `Ali ATT Karimov` | `Ali` / `Karimov ATT` |
| `madina akbarova`, `DILNOZA KARIMOVA` | `Madinaxon` / `Akbarova`, `Dilnozaxon` / `Karimova` |
| `Ustoz Dilnoza Karimova` | `Ustoz Dilnozaxon Karimova` (tartib saqlanadi) |
| `Opa Dilnoza` | `Opa Dilnozaxon` |
| `Madina Dilnoza Akbarova` (noaniq) | o'zgarmaydi |

Skript ishonchi komil bo'lmagan kontaktlarga tegmaydi.

## O'rnatish
```bash
pip install -r requirements.txt
cp .env.example .env      # keyin .env ni oching va haqiqiy TG_API_ID, TG_API_HASH ni yozing
# (yoki: export TG_API_ID=... TG_API_HASH=...)
```

## Ishlatish
```bash
# 1) (ixtiyoriy) ismlarni saytlardan yig'ish -> data/ismlar_hammasi_toliq.csv (GitHub'ga yuklanmaydi)
python ismlar_yigish.py

# 2) (ixtiyoriy) yig'ilgan CSV'dan bazani qayta yaratish -> data/boy_names.json, data/girl_names.json
#    (tayyor baza repoda bor, 1-2 qadamlar shart emas)
python build_name_db.py

# 3) testlar
python -m unittest discover -s tests

# 4) kontaktlar: avval DRY_RUN = True (faqat ko'rsatadi)
python rename_contacts.py
#    hammasi to'g'ri bo'lsa rename_contacts.py da DRY_RUN = False qiling

# 5) xato bo'lsa asl holatiga qaytarish
python restore_contacts.py
```

## Google Contacts (telefon kontaktlari)
Telegram'dagi ismni o'zgartirish telefon (Google) kontaktini o'zgartirmaydi. Manba Google'da bo'lsa, o'sha yerni ham tuzating.

```bash
pip install google-api-python-client google-auth-oauthlib   # credentials.json: google_contacts.py boshidagi qo'llanma
python google_contacts.py api            # faqat ko'rsatadi
python google_contacts.py api --apply    # kontaktlarni joyida yangilaydi (dublikat yaratmaydi)
python google_contacts.py api --relogin  # eski loyiha/akkauntdan chiqib, qaytadan kirish

python google_contacts.py csv contacts.csv   # offlayn: Google CSV eksportini tekshiradi
```
`csv` rejimidagi tuzatilgan faylni Google'ga qayta import qilmang: dublikat yaratishi mumkin. U faqat tekshirish uchun.
Faqat Google akkauntiga sinxronlangan kontaktlar o'zgaradi (telefon xotirasidagilari emas).

## Zaxira
- `contacts_original.json` - birinchi ishga tushirishdagi asl holat (ustidan yozilmaydi)
- `backups/contacts_<vaqt>.json` - har bir ishga tushirishdan oldingi holat
- `google_backups/` - Google kontaktlarining to'liq zaxirasi (api rejimi)

## Sozlamalar (`names_logic.py`)
| Nomi | Ma'nosi |
|---|---|
| `ADD_XON` | qizlar ismiga "xon" qo'shish |
| `SWAP_NAMES` | ism-familiya o'rnini almashtirish |
| `NORMALIZE_STRUCTURE` | ism va familiyani maydonlarga to'g'ri ajratish |
| `SPLIT_FIELDS` | `False` bo'lsa, ko'rinadigan nom o'zgarmaydigan kontaktlar yozilmaydi |
| `FEMALE_EXTRA`, `NOT_NAMES`, `MALE_A` | qo'lda to'ldiriladigan ro'yxatlar |

## Xavfsizlik
`*.session` fayli Telegram hisobingizga kirish kaliti, `contacts_*.json` esa boshqalarning telefon raqamlarini
o'z ichiga oladi. `.gitignore` ularni chiqarib tashlaydi - ularni hech qachon GitHub'ga yuklamang.

## Ma'lumotlar
`data/boy_names.json` va `data/girl_names.json` - ommaviy saytlardan yig'ilgan ismlar ro'yxati (faqat ismlar, ma'nolarsiz).
Saytlarga og'irlik tushirmaslik uchun `ismlar_yigish.py` so'rovlar orasida kutadi; saytlarning foydalanish shartlariga rioya qiling.
