import os
import time
import json
import requests
from datetime import date

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["DATABASE_ID"]
TG_TOKEN = os.environ["TG_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
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
        return ", ".join(f.get("name", "") for f in files)
    return ""

def get_age(birth_str):
    if not birth_str:
        return ""
    try:
        months = {"January":1,"February":2,"March":3,"April":4,"May":5,"June":6,
                  "July":7,"August":8,"September":9,"October":10,"November":11,"December":12}
        if "-" in birth_str:
            year = int(birth_str[:4])
        else:
            parts = birth_str.replace(",", "").split()
            year = int(parts[-1])
        age = date.today().year - year
        return str(age)
    except:
        return ""

def row(icon, label, value):
    if value and str(value).strip():
        return f"{icon} *{label}:* {value}"
    return None

def format_entry(entry):
    props = entry["properties"]
    def g(key):
        return get_text(props.get(key, {}))

    full_name  = g("Full Name")
    phone      = g("Telefon raqami?")
    backup     = g("Zahira telefon raqamingiz?")
    hr_phone   = g("Ohirgi ish joyingizdan Siz haqingizda ma'lumot olish uchun HR yoki rahbariyat telefon raqami?")
    birth      = g("Tug'ilgan sanangiz?")
    age        = get_age(birth) or g("Yoshingiz?")
    address    = g("Yashash manzilingiz [Tuman, MFY, ko'cha, uy]?")
    status     = g("Hozirgi vaqtda ...?")
    family     = g("Oilaviz ahvolingiz?")
    health     = g("Kasalliklaringiz bormi? Bor bo'lsa, bular bo'yicha ma'lumot bering!")
    education  = g("Ma'lumotingiz?")
    university = g("Qaysi o'quv yurtini qaysi yo'nalishini tugatgansiz?")
    years      = g("Qaysi yillarda?")
    english    = g("Ingliz tili bilish darajangiz? ")
    russian    = g("Rus tili bilish darajangiz?")
    other_lang = g("Boshqa qaysi chet tilini bilasiz?")
    computer   = g("Kompyuterdan foydalanish darajangiz?")
    programs   = g("Qaysi kompyuter dasturlarini yuqori darajada bilasiz?")
    last_job   = g("Oxirgi ish joyingiz va bo'shash sababi?")
    prev_jobs  = g("Oldingi ish joylaringiz? Qaysi davrlarda, qaysi tashkilotda va qaysi vazifalarda?")
    achieve    = g("Oldingi ish joylaringizda erishga yutuqlaringiz?")
    why_hire   = g("Nega sizni ishga olishimiz kerak?")
    future     = g("5 yildan keyin o'zingizni qayerda ko'rayapsiz?")
    stay       = g("Bizning korxonada qancha muddat ishlamoqchisiz?")
    credit     = g("Kredit qarzdorligingiz bormi?")
    criminal   = g("Sudlanganmisiz?")
    entered    = g("Bugungi sana")

    birth_display = f"{birth} ({age} yosh)" if birth and age else birth

    lines = [
        f"🆕 *Yangi anketa keldi!*",
        f"📅 *Sana:* {entered}",
        "",
        row("👤", "Ism", full_name),
        row("📞", "Telefon", phone),
        row("📞", "Zahira tel", backup),
        row("📞", "HR tel", hr_phone),
        row("🎂", "Tug'ilgan sana", birth_display),
        row("📍", "Manzil", address),
        "",
        row("💼", "Hozirgi holati", status),
        row("👨‍👩‍👧", "Oilaviy", family),
        row("❤️", "Sog'liq", health),
        "",
        row("🎓", "Ma'lumot", education),
        row("🏫", "O'quv yurti", f"{university} ({years})" if university and years else university),
        "",
        row("🗣", "Ingliz tili", english),
        row("🗣", "Rus tili", russian),
        row("🗣", "Boshqa til", other_lang),
        row("💻", "Kompyuter", computer),
        row("🖥", "Dasturlar", programs),
        "",
        row("🏢", "Oxirgi ish joyi", last_job),
        row("📋", "Oldingi ish joylari", prev_jobs),
        row("🏆", "Yutuqlar", achieve),
        "",
        row("💡", "Nega ishga olish kerak", why_hire),
        row("🔮", "5 yildan keyin", future),
        row("⏳", "Necha muddat ishlaydi", stay),
        "",
        row("💳", "Kredit", credit),
        row("⚖️", "Sudlanganmi", criminal),
    ]

    return "\n".join(line for line in lines if line is not None)

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    })
    if not resp.ok:
        print(f"Telegram xato: {resp.status_code} — {resp.json()}")
    return resp.ok

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
                msg = format_entry(entry)
                if send_telegram(msg):
                    seen.add(entry["id"])
                    print(f"Yuborildi: {entry['id']}")
                else:
                    print(f"Xato: Telegram ga yuborib bo'lmadi")
            save_seen(seen)
        except Exception as e:
            print(f"Xato: {e}")
        time.sleep(30)

if __name__ == "__main__":
    main()
