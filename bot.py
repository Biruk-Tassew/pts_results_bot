import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from datetime import datetime, UTC

URL = "https://corporate.ethiopianairlines.com/AboutEthiopian/careers/results"
STATE_FILE = "ethiopian_results_state.json"

BOT_TOKEN = "8771537045:AAFoqzIqCnIhYULK7Fv5TlWIvriRIzoFXeI"
CHAT_ID = "426450306"


def send_telegram_message(text: str):
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    response = requests.post(api_url, data={
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }, timeout=30)
    response.raise_for_status()


def fetch_page():
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    return response.text


def extract_relevant_content(html: str):
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text("\n", strip=True)

    start_marker = "Result Announcements"
    if start_marker in text:
        text = text[text.index(start_marker):]

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    cleaned = []
    for line in lines:
        if len(line) < 2:
            continue
        cleaned.append(line)

    final_text = "\n".join(cleaned)
    return final_text


def compute_hash(content: str):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_previous_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(content: str, content_hash: str):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "hash": content_hash,
            "content": content,
            "checked_at": datetime.now(UTC).isoformat()
        }, f, ensure_ascii=False, indent=2)


def main():
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")

    html = fetch_page()
    current_content = extract_relevant_content(html)
    current_hash = compute_hash(current_content)

    previous = load_previous_state()

    if previous is None:
        save_state(current_content, current_hash)
        send_telegram_message(
            "Ethiopian Airlines results monitor is now active.\n"
            f"Watching: {URL}"
        )
        return

    if previous["hash"] != current_hash:
        old_content = previous.get("content", "")

        message = (
            "Change detected on Ethiopian Airlines results page.\n"
            f"{URL}\n\n"
            "The page content has changed. Please check the website."
        )

        send_telegram_message(message)
        save_state(current_content, current_hash)
    else:
        print("No change detected.")


if __name__ == "__main__":
    main()