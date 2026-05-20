import os
import time
import json
import requests
from datetime import date

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["DATABASE_ID"]
TG_TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
CHANNEL_ID = os.environ.get("CHANNEL_ID", "")
SEEN_FILE = "seen_ids.json"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(ids), f)

def get_text(prop):
    if not prop:
        return ""
    t = prop.get("type")
    if t == "title":
        return "".join(x["plain_text"] for x in prop.get("title", []))
    elif t == "rich_text":
        return "".join(x["plain_text"] for x in prop.get("rich_text", []))
    elif t == "email":
        return prop.get("email") or ""
    elif t == "phone_number":
        return prop.get("phone_number") or ""
    elif t == "select":
        s = prop.get("select")
        return s["name"] if s else ""
    elif t == "multi_select":
        return ", ".join(x["name"] for x in prop.get("multi_select", []))
    elif t == "number":
        n = prop.get("number")
        return str(int(n)) if n is not None else ""
    elif t == "date":
        d = prop.get("date")
        return d["start"] if d else ""
    elif t == "checkbox":
        return "Ha" if prop.get("checkbox") else "Yo'q"
    elif t == "url":
        return prop.get("url") or ""
    elif t == "files":
        files = prop.get("files", [])
        urls = []
        for f in files:
            if f.get("type") == "external":
                urls.append(f["external"]["url"])
            elif f.get("type") == "file":
                urls.append(f["file"]["url"])
        return urls[0] if urls else ""
    return ""

def get_age(birth_str):
    if not birth_str:
        return ""
    try:
        if "-" in birth_str:
            year = int(birth_str[:4])
        else:
            parts = birth_str.replace(",", "").split()
            year = int(parts[-1])
        return str(date.today().year - year)
    except:
        return ""

def row(icon, label, value):
    if value and str(value).strip():
        return f"{icon} <b>{label}:</b> {value}"
    return None

def format_entry(entry):
    props = entry["properties"]
    def g(key):
        return get_text(props.get(key, {}))

    full_name  = g("Full Name")
    entered    = g("Bugungi sana")
    birth      = g("Tug'ilgan sanangiz?")
    age        = get_age(birth) or g("Yoshingiz?")
    address    = g("Yashash manzilingiz [Tuman, MFY, ko'cha, uy]?")
    phone      = g("Telefon raqami?")
    backup     = g("Zahira telefon raqamingiz?")
    status     = g("Hozirgi vaqtda ...?")
    family     = g("Oilaviz ahvolingiz?")
    russian    = g("Rus tili bilish darajangiz?")
    english    = g("Ingliz tili bilish darajangiz? ")
    other_lang = g("Boshqa qaysi chet tilini bilasiz?")
    computer   = g("Kompyuterdan foydalanish darajangiz?")
    programs   = g("Qaysi kompyuter dasturlarini yuqori darajada bilasiz?")
    education  = g("Ma'lumotingiz?")
    university = g("Qaysi o'quv yurtini qaysi yo'nalishini tugatgansiz?")
    years      = g("Qaysi yillarda?")
    prev_jobs  = g("Oldingi ish joylaringiz? Qaysi davrlarda, qaysi tashkilotda va qaysi vazifalarda?")
    achieve    = g("Oldingi ish joylaringizda erishga yutuqlaringiz?")
    last_job   = g("Oxirgi ish joyingiz va bo'shash sababi?")
    hr_phone   = g("Ohirgi ish joyingizdan Siz haqingizda ma'lumot olish uchun HR yoki rahbariyat telefon raqami?")
    stay       = g("Bizning korxonada qancha muddat ishlamoqchisiz?")
    why_hire   = g("Nega sizni ishga olishimiz kerak?")
    future     = g("5 yildan keyin o'zingizni qayerda ko'rayapsiz?")
    health     = g("Kasalliklaringiz bormi? Bor bo'lsa, bular bo'yicha ma'lumot bering!")
    criminal   = g("Sudlanganmisiz?")
    credit     = g("Kredit qarzdorligingiz bormi?")
    background = g("Personal Background [Tug'ulganingizda hozirgacha barcha ma'lumotlarni yillar kesimida yozib bering]! *")
    photo_url  = g("Photo")

    birth_display = f"{birth} ({age} yosh)" if birth and age else birth

    lines = [
        f"🆕 <b>Yangi anketa!</b>",
        f"📅 <b>Bugungi sana:</b> {entered}",
        "",
        row("👤", "Full Name", full_name),
        row("📞", "Telefon raqami", phone),
        row("📞", "Zahira telefon raqami", backup),
        row("🎂", "Tug'ilgan sanangiz", birth_display),
        row("📍", "Yashash manzilingiz", address),
        "",
        row("💼", "Hozirgi vaqtda", status),
        row("👨‍👩‍👧", "Oilaviy ahvolingiz", family),
        row("🏥", "Kasalliklaringiz", health),
        "",
        row("🎓", "Ma'lumotingiz", education),
        row("🏫", "O'quv yurti / yo'nalish", f"{university} ({years})" if university and years else university),
        "",
        row("🗣", "Rus tili bilish darajasi", russian),
        row("🗣", "Ingliz tili bilish darajasi", english),
        row("🗣", "Boshqa chet tili", other_lang),
        row("💻", "Kompyuterdan foydalanish darajasi", computer),
        row("🖥", "Kompyuter dasturlari", programs),
        "",
        row("🏢", "Oldingi ish joylari", prev_jobs),
        row("🏆", "Erishgan yutuqlar", achieve),
        row("🚪", "Oxirgi ish joyi va bo'shash sababi", last_job),
        row("📞", "HR/rahbariyat telefoni", hr_phone),
        "",
        row("💡", "Nega sizni ishga olishimiz kerak", why_hire),
        row("🔮", "5 yildan keyin", future),
        row("⏳", "Korxonada ishlash muddati", stay),
        "",
        row("💳", "Kredit qarzdorligi", credit),
        row("⚖️", "Sudlanganmi", criminal),
        "",
        row("📖", "Personal Background", background),
    ]

    text = "\n".join(line for line in lines if line is not None)
    return text, photo_url

def send_message(chat_id, text, photo_url):
    base_url = f"https://api.telegram.org/bot{TG_TOKEN}"
    if photo_url:
        resp = requests.post(f"{base_url}/sendPhoto", json={
            "chat_id": chat_id,
            "photo": photo_url,
            "caption": text,
            "parse_mode": "HTML"
        })
        # Agar rasm yuborishda xato — matn sifatida yuboramiz
        if not resp.ok:
            print(f"Rasm xato ({resp.status_code}), matn sifatida yuborilmoqda...")
            resp = requests.post(f"{base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            })
    else:
        resp = requests.post(f"{base_url}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        })
    if not resp.ok:
        print(f"Telegram xato ({chat_id}): {resp.status_code} — {resp.json()}")
    return resp.ok

def send_telegram(text, photo_url):
    success = True
    for chat_id in filter(None, [CHAT_ID, CHANNEL_ID]):
        if not send_message(chat_id, text, photo_url):
            success = False
    return success

def query_database():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    body = {
        "sorts": [{"timestamp": "created_time", "direction": "descending"}],
        "page_size": 20
    }
    resp = requests.post(url, headers=HEADERS, json=body)
    data = resp.json()
    if resp.status_code != 200:
        print(f"Notion API xato: {resp.status_code} — {data}")
    return data.get("results", [])

def main():
    print("Bot ishga tushdi...")
    seen = load_seen()

    if not seen:
        print("Birinchi ishga tushish — mavjud yozuvlar saqlanmoqda...")
        entries = query_database()
        for e in entries:
            seen.add(e["id"])
        save_seen(seen)
        print(f"{len(seen)} ta mavjud yozuv saqlandi. Yangilarini kutmoqda...")

    while True:
        try:
            entries = query_database()
            new_entries = [e for e in entries if e["id"] not in seen]
            for entry in reversed(new_entries):
                text, photo_url = format_entry(entry)
                if send_telegram(text, photo_url):
                    seen.add(entry["id"])
                    print(f"Yuborildi: {entry['id']}")
                else:
                    print(f"Xato: yuborib bo'lmadi")
            save_seen(seen)
        except Exception as e:
            print(f"Xato: {e}")
        time.sleep(30)

if __name__ == "__main__":
    main()
