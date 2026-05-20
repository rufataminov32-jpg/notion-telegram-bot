import os
import time
import json
import requests

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
        return str(n) if n is not None else ""
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

def format_entry(entry):
    props = entry["properties"]

    # Asosiy ma'lumotlar
    full_name = get_text(props.get("Full Name", {}))
    phone = get_text(props.get("Telefon raqami?", {}))
    backup_phone = get_text(props.get("Zahira telefon raqamingiz?", {}))
    age = get_text(props.get("Yoshingiz?", {}))
    birth = get_text(props.get("Tug'ilgan sanangiz?", {}))
    address = get_text(props.get("Yashash manzilingiz [Tuman, MFY, ko'cha, uy]?", {}))
    education = get_text(props.get("Ma'lumotingiz?", {}))
    university = get_text(props.get("Qaysi o'quv yurtini qaysi yo'nalishini tugatgansiz?", {}))
    years = get_text(props.get("Qaysi yillarda?", {}))
    status = get_text(props.get("Hozirgi vaqtda ...?", {}))
    family = get_text(props.get("Oilaviz ahvolingiz?", {}))
    last_job = get_text(props.get("Oxirgi ish joyingiz va bo'shash sababi?", {}))
    english = get_text(props.get("Ingliz tili bilish darajangiz? ", {}))
    russian = get_text(props.get("Rus tili bilish darajangiz?", {}))
    computer = get_text(props.get("Kompyuterdan foydalanish darajangiz?", {}))
    programs = get_text(props.get("Qaysi kompyuter dasturlarini yuqori darajada bilasiz?", {}))
    credit = get_text(props.get("Kredit qarzdorligingiz bormi?", {}))
    criminal = get_text(props.get("Sudlanganmisiz?", {}))
    date = get_text(props.get("Bugungi sana", {}))

    lines = [
        f"🆕 *Yangi anketa keldi!*",
        f"",
        f"👤 *Ism:* {full_name}",
        f"📅 *Sana:* {date}",
        f"",
        f"📞 *Telefon:* {phone}",
        f"📞 *Zahira tel:* {backup_phone}",
        f"🎂 *Tug'ilgan sana:* {birth} ({age} yosh)",
        f"📍 *Manzil:* {address}",
        f"",
        f"💼 *Hozirgi holati:* {status}",
        f"👨‍👩‍👧 *Oilaviy:* {family}",
        f"",
        f"🎓 *Ma'lumot:* {education}",
        f"🏫 *O'quv yurti:* {university} ({years})",
        f"",
        f"🗣 *Ingliz tili:* {english}",
        f"🗣 *Rus tili:* {russian}",
        f"💻 *Kompyuter:* {computer}",
        f"🖥 *Dasturlar:* {programs}",
        f"",
        f"🏢 *Oxirgi ish joyi:* {last_job}",
        f"",
        f"💳 *Kredit:* {credit}",
        f"⚖️ *Sudlanganmi:* {criminal}",
    ]
    return "\n".join(line for line in lines if not line.endswith(": "))

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    })
    return resp.ok

def query_database():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    body = {
        "sorts": [{"timestamp": "created_time", "direction": "descending"}],
        "page_size": 20
    }
    resp = requests.post(url, headers=HEADERS, json=body)
    data = resp.json()
    if "error" in data or resp.status_code != 200:
        print(f"Notion API xato: {resp.status_code} — {data}")
    else:
        print(f"Notion API: {len(data.get('results', []))} ta yozuv topildi")
    return data.get("results", [])

def main():
    print("Bot ishga tushdi...")
    seen = load_seen()

    # Birinchi ishga tushganda mavjud yozuvlarni "ko'rilgan" deb belgilash
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

            for entry in reversed(new_entries):  # Eskidan yangiga
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
