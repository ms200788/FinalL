import os
import secrets
import string
import asyncio
import urllib.parse
import urllib.request
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")

TXT_FILE = "database.txt"

# ================= MEMORY STORAGE =================
funnels = {}
lock = asyncio.Lock()

# ================= LOAD DATA =================
if os.path.exists(TXT_FILE):
    with open(TXT_FILE, "r") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) == 3:
                slug, redirect, link = parts
                funnels[slug] = (redirect, link)

# ================= UTILS =================
def generate_slug():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

def generate_redirect():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

async def save_funnel(slug, redirect, link):
    async with lock:
        funnels[slug] = (redirect, link)
        with open(TXT_FILE, "a") as f:
            f.write(f"{slug}|{redirect}|{link}\n")

async def get_by_slug(slug):
    async with lock:
        return funnels.get(slug)

async def get_by_redirect(redirect, slug):
    async with lock:
        data = funnels.get(slug)
        if data and data[0] == redirect:
            return data
        return None

# ================= TELEGRAM =================
async def send_message(chat_id, text):
    if not BOT_TOKEN:
        return
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text
    }).encode()
    try:
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=data,
            timeout=10
        )
    except:
        pass

async def send_to_channel(text):
    if not BOT_TOKEN or not CHANNEL_ID:
        return
    data = urllib.parse.urlencode({
        "chat_id": CHANNEL_ID,
        "text": text
    }).encode()
    try:
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=data,
            timeout=10
        )
    except:
        pass

# ================= AUTO WEBHOOK SETUP =================
async def setup_webhook():
    if not BOT_TOKEN or not BASE_URL:
        print("Missing BOT_TOKEN or BASE_URL")
        return
    try:
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook",
            timeout=10
        )
        webhook_url = f"{BASE_URL}/webhook"
        response = urllib.request.urlopen(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}",
            timeout=10
        )
        result = json.loads(response.read().decode())
        print("Webhook setup:", result)
    except Exception as e:
        print("Webhook setup failed:", e)

@app.on_event("startup")
async def startup_event():
    await setup_webhook()

# ================= HEALTH =================
@app.get("/health")
async def health():
    return {"status": "alive"}

# ================= WEBHOOK =================
@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    if "message" not in data:
        return {"ok": True}

    message = data["message"]
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    text = message.get("text", "")

    if user_id != OWNER_ID:
        await send_message(chat_id, "Not authorized.")
        return {"ok": True}

    if text.startswith("/create"):
        parts = text.split(" ", 1)
        if len(parts) != 2:
            await send_message(chat_id, "Usage:\n/create https://example.com")
            return {"ok": True}

        link = parts[1].strip()

        slug = generate_slug()
        redirect = generate_redirect()
        await save_funnel(slug, redirect, link)

        await send_to_channel(f"{slug}|{redirect}|{link}")

        await send_message(chat_id, f"User URL:\n{BASE_URL}/u/{slug}")
        await send_message(chat_id, f"Redirect URL:\n{BASE_URL}/r/{redirect}/{slug}")

    return {"ok": True}

# ================= USER PAGE =================
@app.get("/u/{slug}", response_class=HTMLResponse)
async def user_page(slug: str):
    funnel = await get_by_slug(slug)
    if not funnel:
        return HTMLResponse("Page Not Found", status_code=404)

    redirect = funnel[0]

    return f"""
    <html>
    <head>
    <title>Crypto Wealth Secrets</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script>
    let verified = false;

    function startTimer() {{
        let t = 20;
        let timer = setInterval(()=> {{
            document.getElementById("t").innerText = t;
            if(t<=0) {{
                clearInterval(timer);
                document.getElementById("verifyBox").style.display="block";
            }}
            t--;
        }}, 1000);
    }}

    function verifyNow() {{
        if(verified) return;
        verified=true;
        window.open("https://mlinks-pgds.onrender.com/go/NVDOEC","_blank");
        document.getElementById("continueBox").style.display="block";
    }}

    window.onload = startTimer;
    </script>
    </head>
    <body style="font-family:Arial;background:#0f2027;color:#fff;padding:20px;">
        <h1>Crypto Wealth Secrets</h1>
        <p>Please wait <b id="t">20</b> seconds...</p>

        <div id="verifyBox" style="display:none;">
            <button onclick="verifyNow()">Unlock Premium Guide</button>
        </div>

        <div id="continueBox" style="display:none;margin-top:20px;">
            <a href="{BASE_URL}/r/{redirect}/{slug}">
                <button>Continue to Investment Portal</button>
            </a>
        </div>
    </body>
    </html>
    """

# ================= REDIRECT =================
@app.get("/r/{redirect}/{slug}")
async def redirect_page(redirect: str, slug: str):
    funnel = await get_by_redirect(redirect, slug)
    if not funnel:
        return HTMLResponse("Invalid Link", status_code=403)
    return RedirectResponse(funnel[1])