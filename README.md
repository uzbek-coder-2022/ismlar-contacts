# ismlar-contacts

O'zbekcha ismlar bazasi va kontaktlarni (Telegram + Google/telefon) tartibga soluvchi vositalar.

**Nima qiladi**
- kirill -> lotin; `o'`, `g'`, `sh`, `ch` -> `ö`, `ğ`, `ş`, `ç`
- ism va familiya almashib qolgan bo'lsa to'g'rilaydi: `Rahimova | Madina ATT` -> `Madinaxon | Rahimova ATT`
- ism va familiya bitta maydonda bo'lsa ajratadi: `Zilola Saidova | DI` -> `Zilolaxon | Saidova DI`
- qiz ismiga `xon` qo'shadi (yigitlar uchun ham ism-familiya tartibi to'g'rilanadi)
- `madina akbarova` -> `Madinaxon Akbarova`, `DILNOZA KARIMOVA` -> `Dilnozaxon Karimova`

> Vosita kontaktlarni **o'zgartiradi**. Har doim avval `DRY_RUN` (faqat ko'rsatish) rejimida ishga tushiring.
> Zaxira avtomatik saqlanadi, lekin baribir muhim kontaktlaringizni alohida eksport qilib qo'ying.

---

## Mundarija
1. [O'rnatish](#1-ornatish)
2. [Telegram kontaktlari](#2-telegram-kontaktlari)
3. [Google (telefon) kontaktlari - to'liq sozlash](#3-google-telefon-kontaktlari---toliq-sozlash)
4. [Qoidalar: "xon" qachon qo'shiladi](#4-qoidalar-xon-qachon-qoshiladi)
5. [Ism bazasi va qo'lda to'ldirish](#5-ism-bazasi-va-qolda-toldirish)
6. [Sozlamalar](#6-sozlamalar)
7. [Zaxira va qaytarish](#7-zaxira-va-qaytarish)
8. [Muammolar va yechimlar](#8-muammolar-va-yechimlar)
9. [Xavfsizlik](#9-xavfsizlik)
10. [Fayllar tuzilmasi](#10-fayllar-tuzilmasi)

---

## 1. O'rnatish
Python 3.9 yoki yangisi kerak.

```bash
git clone https://github.com/FOYDALANUVCHI/ismlar-contacts.git
cd ismlar-contacts
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m unittest discover -s tests     # testlar: "OK" chiqishi kerak
```

---

## 2. Telegram kontaktlari

### 2.1. API kalitlarini olish (bir marta)
1. https://my.telegram.org saytiga telefon raqamingiz bilan kiring.
2. **API development tools** bo'limini oching.
3. Ilova yarating (App title va Short name - istalgan nom, Platform - Desktop).
4. **api_id** (raqam) va **api_hash** (uzun harf-raqam) ni nusxalang.

### 2.2. `.env` faylini sozlash
```bash
cp .env.example .env
```
`.env` ni oching va haqiqiy qiymatlarni yozing:
```
TG_API_ID=1234567
TG_API_HASH=0123456789abcdef0123456789abcdef
```
- `.env` skriptlar bilan **bir papkada** bo'lishi kerak.
- Namunaviy qiymatlar (`123456`, `your_api_hash`) qolsa, skript to'xtab, xabar beradi.
- `.env` GitHub'ga yuklanmaydi (`.gitignore`da).

### 2.3. Ishga tushirish
```bash
python rename_contacts.py
```
- Birinchi marta Telegram telefon raqamingizni va kelgan kodni so'raydi (terminalda yozasiz). Shundan so'ng `userbot.session` fayli yaratiladi va keyingi safar so'ramaydi.
- `rename_contacts.py` ichida `DRY_RUN = True` turibdi: faqat "eski -> yangi" ro'yxatini chiqaradi, hech narsani o'zgartirmaydi.
- Ro'yxat to'g'ri bo'lsa, `DRY_RUN = False` qiling va qayta ishga tushiring.
- Muammoli kontaktlar `problems_report.txt` fayliga yoziladi.

> Telegram'dagi nom faqat Telegram ichida o'zgaradi. Telefon (Google) kontaktlari alohida - 3-bo'limga qarang.

---

## 3. Google (telefon) kontaktlari - to'liq sozlash

Skript **Google People API** orqali kontaktlarni Google ichida **joyida** yangilaydi (yangi nusxa/dublikat yaratmaydi).
Telefoningiz Google akkaunt bilan sinxronlangan bo'lsa, o'zgarish telefonga ham keladi.

> Faqat **Google akkauntga saqlangan** kontaktlar o'zgaradi. "Telefon" yoki "SIM" xotirasida saqlanganlari
> Google'da ko'rinmaydi, skript ularga tegmaydi. Tekshirish: Kontaktlar ilovasida kontaktni oching,
> qaysi akkauntda saqlanganini ko'rasiz.

### 3.1. Google Cloud loyihasini yaratish
1. https://console.cloud.google.com saytiga **telefondagi kontaktlar bog'langan Google akkaunt** bilan kiring.
2. Yuqoridagi loyiha tanlagichni (chap tepada) bosing -> **New project**.
3. Nom bering (masalan, `ismlar-contacts`) -> **Create**.
4. Loyiha yaratilgach, yuqoridagi tanlagichdan **shu loyihani** tanlang. Keyingi barcha qadamlar shu loyiha ichida bo'ladi.

### 3.2. People API'ni yoqish
1. Chap menyu: **APIs & Services -> Library**.
2. Qidiruvga `People API` yozing, natijani oching.
3. **Enable** tugmasini bosing.

### 3.3. OAuth ruxsat ekranini sozlash
Menyu nomi Google tomonidan vaqti-vaqti bilan o'zgaradi: **APIs & Services -> OAuth consent screen** yoki
**Google Auth Platform**.

1. **Get started** (yoki **Configure consent screen**) ni bosing.
2. **App name**: istalgan (masalan, `ismlar-contacts`). **User support email**: o'z Gmail manzilingiz.
3. **Audience / User type**: **External** ni tanlang.
4. **Contact information**: o'z email manzilingiz. Shartlarga rozilik bering -> **Create**.
5. **Test users** (yoki **Audience -> Test users**) bo'limida **Add users** -> **o'z Gmail manzilingizni** qo'shing.
   *Bu qadam majburiy: aks holda kirishda "Access blocked / 403: access_denied" xatosi chiqadi.*
6. (Ixtiyoriy) **Data Access -> Add or remove scopes** da `.../auth/contacts` (People API / Contacts) ni qo'shing.
7. Ilovani **Publish qilmang**: "Testing" holatida qolaversin (faqat o'zingiz uchun).

### 3.4. `credentials.json` ni yuklab olish
1. **APIs & Services -> Credentials** (yoki Google Auth Platform -> Clients).
2. **Create credentials -> OAuth client ID** (yoki **Create client**).
3. **Application type**: **Desktop app**. Nom: istalgan -> **Create**.
4. Chiqqan oynada **Download JSON** ni bosing.
5. Yuklangan faylni **`credentials.json`** deb qayta nomlang va loyiha papkasiga (`google_contacts.py` yoniga) qo'ying.

### 3.5. Kutubxonalarni o'rnatish
Ular `requirements.txt` ichida bor, `pip install -r requirements.txt` bajargan bo'lsangiz, tayyor. Alohida:
```bash
pip install google-api-python-client google-auth-oauthlib
```

### 3.6. Birinchi ishga tushirish (faqat ko'rish)
```bash
python google_contacts.py api
```
1. Terminalda **Google Cloud loyiha raqami** chiqadi: uni Cloud Console'dagi loyihangiz raqami bilan solishtiring.
2. Brauzer ochiladi: **to'g'ri Google akkauntni tanlang** (tanlash oynasi har safar chiqadi).
3. "Google hasn't verified this app" ogohlantirishi chiqadi (bu o'zingiz yaratgan ilova bo'lgani uchun normal):
   **Advanced -> Go to ... (unsafe)** -> kontaktlarga ruxsat bering -> **Continue**.
4. "The authentication flow has completed" yozuvi chiqsa, brauzerni yopib, terminalga qayting.
5. Terminal "eski -> yangi" ro'yxatini chiqaradi. **Hech narsa o'zgarmaydi**, faqat `google_backups/` ga zaxira saqlanadi.

### 3.7. Haqiqatan yangilash
Ro'yxat to'g'ri bo'lsa:
```bash
python google_contacts.py api --apply
```
Kontaktlar 50 tadan paketlab yangilanadi. Oxirida "Yangilandi: N ta" chiqadi.

### 3.8. Telefonga yetkazish
- Kontaktlar ilovasi -> Sozlamalar -> hisobingizni tanlang -> sinxronlash yoqilgan bo'lsin.
- Android: Sozlamalar -> Google -> Kontaktlarni sinxronlash -> **Hozir sinxronlash**.
- Natijani https://contacts.google.com saytida ham ko'rishingiz mumkin. Yangilanish bir necha daqiqa kechikishi mumkin.

### 3.9. Google buyruqlari
| Buyruq | Nima qiladi |
|---|---|
| `python google_contacts.py api` | faqat ko'rsatadi, zaxira saqlaydi |
| `python google_contacts.py api --apply` | kontaktlarni joyida yangilaydi |
| `python google_contacts.py api --relogin` | eski kirishni (`token.json`) o'chirib, akkauntni qaytadan tanlatadi |
| `python google_contacts.py csv contacts.csv` | offlayn: Google CSV eksportini tekshiradi, o'zgarishlar ro'yxatini yozadi |

`csv` rejimida tuzatilgan faylni Google'ga **qayta import qilmang**: dublikat yaratishi mumkin. U faqat tekshirish uchun.

### 3.10. Eski loyiha yoki akkauntga kirib ketsa
`token.json` avval olingan kirishni eslab qoladi. Skript uni `credentials.json` bilan solishtiradi va boshqa loyiha bo'lsa, o'zi o'chiradi.
Baribir eski akkauntga kirsa:
```bash
python google_contacts.py api --relogin
```
yoki `token.json` ni qo'lda o'chiring va brauzerda to'g'ri akkauntni tanlang.

### 3.11. Google xatolari
| Xabar | Sabab / yechim |
|---|---|
| `Access blocked` / `403: access_denied` | Gmail manzilingiz **Test users** ro'yxatida emas (3.3, 5-qadam) |
| `People API has not been used ... or it is disabled` | People API yoqilmagan yoki boshqa loyiha tanlangan (3.2); yoqqach 1-5 daqiqa kuting |
| `invalid_grant` / `Token has been expired or revoked` | "Testing" holatidagi ilovaning kirishi taxminan 7 kundan keyin tugaydi: `--relogin` qiling |
| `credentials.json topilmadi` | Fayl nomi va joyi to'g'rimi tekshiring (3.4) |
| `O'zgaradi: 0 ta` | Hamma nom allaqachon tartibda yoki kontaktlar Google'da emas (telefon/SIM xotirasida) |
| `Google kontaktlar: 0 ta` | Noto'g'ri akkaunt tanlangan: `--relogin` qiling |
| `429` / limit | Skript 30 soniya kutib qayta urinadi; takrorlansa, birozdan keyin qayta ishga tushiring |
| Brauzer ochilmaydi | Skript brauzer bor kompyuterda ishga tushirilishi kerak (serverda emas) |

### 3.12. Google'ni asliga qaytarish
- Har bir `api` ishga tushirishda to'liq zaxira `google_backups/google_contacts_<vaqt>.json` ga saqlanadi (eski ismlar shu yerda).
- Tez qaytarish uchun Google'ning o'zi: https://contacts.google.com -> **Sozlamalar (⚙) -> Undo changes** (oxirgi 30 kun ichidagi holatga qaytaradi).

---

## 4. Qoidalar: "xon" qachon qo'shiladi
Jins quyidagi tartibda aniqlanadi:
1. **Ism bazasi** (`data/boy_names.json`, `data/girl_names.json`) va qo'lda yozilgan `extra_*.txt` fayllari.
2. **Familiya qo'shimchasi**: `-ova`, `-eva`, `-yeva` = qiz; `-ov`, `-ev`, `-yev` = yigit.
3. Boshqa hech narsa: ism bazada yo'q va familiya ham dalil bermasa, **"xon" qo'shilmaydi**
   (ism oxiriga qarab taxmin qilinmaydi, shuning uchun `Usluga`, `Pochta`, `Melodiya` kabi so'zlar o'zgarmaydi).

Ism ikkala ro'yxatda ham bo'lsa (noaniq), "xon" qo'shilmaydi, familiyada `-ova`/`-ov` bo'lsa, shunga qarab hal qilinadi.

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
| `Usluga` / `DJ`, `Pochta` / `Aloqa` | o'zgarmaydi (ism emas) |
| `Madina Dilnoza Akbarova` (noaniq) | o'zgarmaydi |

Skript ishonchi komil bo'lmagan kontaktlarga tegmaydi.

---

## 5. Ism bazasi va qo'lda to'ldirish
Baza: `data/boy_names.json` va `data/girl_names.json` (~13 400 o'g'il, ~7 000 qiz ismi; faqat ismlar, ma'nosiz).

Kodni tahrirlamasdan, `data/` papkasidagi matn fayllariga yozing (har qatorda bitta ism, `#` dan keyin izoh):

| Fayl | Nima yoziladi | Natija |
|---|---|---|
| `data/extra_girl_names.txt` | bazada yo'q yoki noaniq qiz ismlari | "xon" qo'shiladi |
| `data/extra_boy_names.txt` | bazada yo'q yoki noaniq o'g'il bola ismlari | ism sifatida taniladi, "xon" qo'shilmaydi |
| `data/extra_not_names.txt` | ism bo'lmagan so'zlar (`usluga`, `admin`) | tegilmaydi |

- Ismni "xon"siz yozing: `Zorinta`, `Zorintaxon` emas.
- Harf turi, apostrof, `ö`, `ş`, `x`/`h` muhim emas.
- Noaniq ismni faqat `extra_girl_names.txt` ga yozsangiz - qiz, faqat `extra_boy_names.txt` ga yozsangiz - o'g'il bola deb olinadi (bazadan ustun). Ikkala faylga yozsangiz - yana noaniq.
- Fayllar `data/` papkasida bo'lishi shart (loyiha papkasining o'zida emas). Skriptni qayta ishga tushiring.

**Bazani saytlardan yangilash (ixtiyoriy)**
```bash
python ismlar_yigish.py                  # -> data/ismlar_hammasi_toliq.csv (GitHub'ga yuklanmaydi)
python build_name_db.py                  # CSV'dan boy_names/girl_names ni qayta yaratadi
```
Skript so'rovlar orasida kutadi; saytlarning foydalanish shartlariga rioya qiling.
Yuklanmagan sahifalar `yuklanmagan_sahifalar.txt` ga yoziladi: skriptni qayta ishga tushirsangiz, yetishmaganlari to'ldiriladi.

---

## 6. Sozlamalar
`names_logic.py` boshida:

| Nomi | Ma'nosi | Standart |
|---|---|---|
| `ADD_XON` | qizlar ismiga "xon" qo'shish | `True` |
| `SWAP_NAMES` | ism-familiya o'rnini almashtirish | `True` |
| `NORMALIZE_STRUCTURE` | ism va familiyani maydonlarga to'g'ri ajratish | `True` |
| `FIX_CASE` | `madina` -> `Madina`, `DILNOZA` -> `Dilnoza` | `True` |
| `SPLIT_FIELDS` | `False` bo'lsa, ko'rinadigan nom o'zgarmaydigan (faqat maydon chegarasi o'zgaradigan) kontaktlar yozilmaydi | `True` |

`rename_contacts.py` boshida: `DRY_RUN` (`True` = faqat ko'rsatadi).

---

## 7. Zaxira va qaytarish
| Fayl / papka | Nima |
|---|---|
| `contacts_original.json` | Telegram kontaktlarining birinchi ishga tushirishdagi asl holati (ustidan yozilmaydi) |
| `backups/contacts_<vaqt>.json` | Telegram: har bir ishga tushirishdan oldingi holat |
| `google_backups/google_contacts_<vaqt>.json` | Google: har bir `api` ishga tushirishdagi to'liq holat |

**Telegram'ni qaytarish**
```bash
python restore_contacts.py                                   # contacts_original.json dan (DRY_RUN: faqat ko'rsatadi)
python restore_contacts.py backups/contacts_20250101_120000.json
```
`restore_contacts.py` ichida `DRY_RUN = False` qilsangiz, haqiqatan qaytaradi.
Google uchun 3.12-bo'limga qarang.

---

## 8. Muammolar va yechimlar
| Muammo | Yechim |
|---|---|
| `TG_API_ID va TG_API_HASH topilmadi` | `.env` yarating (2.2); fayl skript bilan bir papkada bo'lsin |
| `.env da namunaviy qiymatlar turibdi` | `123456` / `your_api_hash` o'rniga haqiqiy qiymatlarni yozing |
| `FloodWait` / "Kutish kerak" | Telegram limiti: skript kutib, bir marta qayta uriniladi; qolganlari `problems_report.txt` da |
| Telefonda nomlar o'zgarmadi | Telegram skripti faqat Telegram'ni o'zgartiradi; telefon uchun 3-bo'lim |
| "xon" qo'shilmadi | Ism bazada yo'q yoki noaniq: `data/extra_girl_names.txt` ga yozing (5) |
| Ism bo'lmagan so'zga "xon" qo'shildi | `data/extra_not_names.txt` ga yozing; avval qo'shilganini `restore_contacts.py` bilan qaytaring |
| `Ism bazasi: 0 ta` / `baza juda kichik` | `data/boy_names.json` va `girl_names.json` borligini tekshiring (yoki `python build_name_db.py`) |

---

## 9. Xavfsizlik
Quyidagi fayllar **hech qachon** GitHub'ga yuklanmasligi kerak (`.gitignore` ularni chiqarib tashlaydi):

| Fayl | Nega xavfli |
|---|---|
| `.env` | Telegram API kalitlari |
| `*.session` (`userbot.session`) | Telegram hisobingizga to'liq kirish kaliti |
| `credentials.json`, `token.json` | Google kirish kalitlari |
| `contacts_original.json`, `backups/`, `google_backups/` | boshqa odamlarning ismlari va telefon raqamlari |

Push qilishdan oldin `git status` va `git ls-files` bilan bu fayllar ro'yxatda yo'qligini tekshiring.
Agar ular tasodifan yuklangan bo'lsa: Telegram'da (Sozlamalar -> Qurilmalar) seansni tugating, Google Cloud'da OAuth clientni o'chirib yangisini yarating va git tarixini tozalang.

---

## 10. Fayllar tuzilmasi
```
ismlar-contacts/
├── rename_contacts.py     Telegram kontaktlarini o'zgartiradi
├── restore_contacts.py    Telegram kontaktlarini zaxiradan qaytaradi
├── google_contacts.py     Google kontaktlari (api / csv rejimlari)
├── names_logic.py         ism-familiya, jins va "xon" mantig'i (sozlamalar shu yerda)
├── transliterate.py       kirill -> lotin
├── build_name_db.py       CSV'dan ism bazasini yasaydi
├── ismlar_yigish.py       saytlardan ismlarni yig'adi
├── env_loader.py          .env o'qigich
├── data/
│   ├── boy_names.json|csv, girl_names.json|csv     ism bazasi
│   └── extra_girl_names.txt, extra_boy_names.txt, extra_not_names.txt   qo'lda to'ldiriladigan ro'yxatlar
├── tests/                 avtomatik testlar
├── .env.example           .env namunasi
└── requirements.txt
```
