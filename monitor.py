import os
import requests
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime, UTC

URL = "https://corporate.ethiopianairlines.com/AboutEthiopian/careers/results"

# GitHub Gist info
GIST_ID = os.getenv("GIST_ID")  # create empty gist first
PAT_GITHUB = os.getenv("PAT_GITHUB")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


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
    cleaned = [line for line in lines if len(line) > 1]
    return "\n".join(cleaned)


def compute_hash(content: str):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_previous_hash():
    headers = {"Authorization": f"token {PAT_GITHUB}"}
    url = f"https://api.github.com/gists/{GIST_ID}"
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    gist = r.json()
    content = gist["files"]["state.json"]["content"]
    return content.strip() if content else None


def save_current_hash(current_hash: str):
    headers = {"Authorization": f"token {PAT_GITHUB}"}
    url = f"https://api.github.com/gists/{GIST_ID}"
    data = {
        "files": {
            "state.json": {
                "content": current_hash
            }
        }
    }
    r = requests.patch(url, headers=headers, json=data, timeout=30)
    r.raise_for_status()


def main():
    if not BOT_TOKEN or not CHAT_ID:
        raise ValueError("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
    if not GIST_ID or not PAT_GITHUB:
        raise ValueError("Set GIST_ID and PAT_GITHUB")

    html = fetch_page()
    content = extract_relevant_content(html)
    current_hash = compute_hash(content)

    previous_hash = load_previous_hash()

    if previous_hash != current_hash:
        send_telegram_message(
            f"Ethiopian Airlines results page changed!\n{URL}"
        )
        save_current_hash(current_hash)
    else:
        print("No change detected.")


if __name__ == "__main__":
    main()