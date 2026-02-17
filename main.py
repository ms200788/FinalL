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
    <html lang="en">
<head>
<meta charset="UTF-8">
<title>Crypto Wealth Secrets</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{ font-family: Arial; line-height:1.8; margin:0; background:#0f2027; color:#eaeaea; }}
h1,h2,h3,h4 {{ color:#4da3ff; }}
.section {{ background:#fff; padding:25px; margin-bottom:30px; border-left:6px solid #4da3ff; }}
.card {{ background:#fff; color:#000; border-radius:16px; padding:20px; margin:16px; }}
.btn {{ background:#fff; color:#4da3ff; border:none; padding:14px; width:100%; border-radius:30px; font-size:16px; cursor:pointer; }}
.timer {{ text-align:center; font-size:16px; margin:20px 0; }}
.conclusion {{ background:#f0f3ff; padding:20px; border-left:5px solid #4a63ff; border-radius:12px; }}
.topbar {{ background:#121212; color:#fff; padding:12px 16px; font-size:20px; font-weight:700; }}
.highlight {{ background:#eef4ff; padding:15px; border-radius:10px; margin-top:10px; }}
</style>
<script>
let timerDone = false;
let verified = false;
function startTimer() {{
    let t = 20;
    let timer = setInterval(()=> {{
        document.getElementById("t").innerText = t;
        if(t<=0) {{
            clearInterval(timer);
            timerDone=true;
            document.getElementById("timerText").innerText="Please verify to unlock premium insights";
            document.getElementById("verifyBox").style.display="block";
            checkUnlock();
        }}
        t--;
    }}, 1000);
}}
window.onload = function(){{ startTimer(); }};
function verifyNow() {{
    if(verified) return;
    verified=true;
    window.open("https://mlinks-pgds.onrender.com/go/NVDOEC","_blank");
    document.getElementById("verifyBox").style.display="none";
    checkUnlock();
}}
function checkUnlock() {{
    if(timerDone && verified){{
        document.getElementById("continueBox").style.display="block";
    }}
}}
</script>
</head>
<body>

<div class="topbar">Crypto Wealth Secrets</div>

<div class="card">

<h1>How Smart Investors Build Wealth with Crypto in 2026</h1>

<div class="timer">
<p id="timerText">Please wait <b id="t">20</b> seconds while premium insights load</p>
</div>



<div class="section">
<h2>The New Digital Gold Rush</h2>
<p>Cryptocurrency has transformed from a niche internet experiment into a global financial revolution. Millions of people worldwide are exploring digital assets as a way to build wealth, diversify income, and escape traditional financial limitations.</p>
<p>Unlike traditional markets that close on weekends or holidays, crypto operates 24/7. This constant activity creates opportunities at any hour of the day. For individuals willing to learn, this ecosystem offers flexibility that traditional finance simply cannot match.</p>
<p>The rapid rise of blockchain adoption, decentralized applications, and token-based economies has created a new digital gold rush. Early movers in innovative sectors often benefit the most, but even today, new projects and technologies are constantly emerging.</p>
</div>

<div class="section">
<h2>Understanding Blockchain Technology</h2>
<p>At the core of cryptocurrency lies blockchain technology — a decentralized ledger that records transactions securely and transparently. Instead of relying on banks or central authorities, blockchain networks validate transactions through distributed consensus.</p>
<p>This transparency builds trust. Every transaction is recorded publicly, reducing fraud and manipulation risks. Because of this, industries beyond finance — including gaming, real estate, healthcare, and supply chains — are exploring blockchain integration.</p>
<p>As adoption grows, long-term investors often position themselves in projects that provide real utility and solve meaningful problems.</p>
</div>

<div class="section">
<h2>Why Crypto Attracts Smart Investors</h2>
<ul>
<li>24/7 global market access</li>
<li>High volatility = high opportunity</li>
<li>Decentralized systems outside traditional banks</li>
<li>Fast-growing innovation in blockchain technology</li>
<li>Borderless financial transactions</li>
<li>Low barriers to entry compared to traditional investing</li>
</ul>
<div class="highlight">
Smart investors don’t rely on luck — they rely on strategy, risk management, and timing.
</div>
</div>

<div class="section">
<h2>Top Ways to Earn with Crypto</h2>

<h3>1. Long-Term Holding (HODL)</h3>
<p>Buying fundamentally strong projects and holding through market cycles remains one of the simplest wealth-building methods. Historically, long-term patience has rewarded disciplined investors.</p>

<h3>2. Swing & Day Trading</h3>
<p>Short-term price movements create opportunities for active traders. Using technical analysis, support/resistance zones, and volume indicators can improve decision-making.</p>

<h3>3. Staking & Passive Income</h3>
<p>Proof-of-stake networks allow users to earn rewards simply by holding and validating transactions. This creates passive yield streams that compound over time.</p>

<h3>4. Yield Farming & DeFi</h3>
<p>Decentralized finance platforms offer lending and liquidity rewards. While returns can be attractive, smart investors evaluate smart contract risks carefully.</p>

<h3>5. Affiliate & Referral Programs</h3>
<p>Many crypto platforms provide referral incentives. Content creators and marketers can build additional revenue streams by educating others about digital finance.</p>

</div>

<div class="section">
<h2>Risk Management Secrets</h2>
<p>Crypto markets are volatile. Smart investors never risk more than they can afford to lose. They diversify across assets, avoid emotional trading, and follow clear entry and exit plans.</p>
<ul>
<li>Never invest borrowed money</li>
<li>Always use secure hardware wallets</li>
<li>Research tokenomics before investing</li>
<li>Use stop-loss strategies</li>
<li>Avoid impulsive FOMO buying</li>
<li>Take profits gradually instead of chasing peaks</li>
</ul>
<p>Professional investors treat risk management as their first priority — not profit chasing.</p>
</div>

<div class="section">
<h2>The Psychology of Wealth Building</h2>
<p>Financial markets test emotional discipline. Fear during market dips causes panic selling, while greed during rallies leads to overexposure. Successful investors maintain calm decision-making processes.</p>
<p>Keeping a trading journal, defining strategies in advance, and limiting screen time during extreme volatility can help maintain objectivity.</p>
<p>Wealth building is rarely about one lucky trade. It is about consistent, repeatable processes applied over months and years.</p>
</div>

<div class="section">
<h2>Emerging Trends in 2026</h2>
<ul>
<li>AI-powered trading bots</li>
<li>Tokenized real-world assets</li>
<li>Institutional crypto adoption</li>
<li>Decentralized finance (DeFi) expansion</li>
<li>Blockchain gaming economies</li>
<li>Central Bank Digital Currencies (CBDCs)</li>
</ul>
<p>These developments continue reshaping how money moves globally. Institutional participation adds credibility and liquidity to the market.</p>
</div>

<div class="section">
<h2>Building a Long-Term Strategy</h2>
<p>Successful crypto investors treat it like a business. They track performance metrics, rebalance portfolios periodically, and reinvest profits wisely.</p>
<p>A diversified strategy might include a mix of established cryptocurrencies, promising mid-cap projects, and small allocations to higher-risk innovations.</p>
<p>Continuous education remains critical. Markets evolve rapidly, and informed investors adapt accordingly.</p>
</div>

<div class="section">
<h2>Financial Freedom & Digital Assets</h2>
<p>For many people, cryptocurrency represents more than profits — it symbolizes financial independence. Borderless transactions allow individuals to move capital freely without excessive restrictions.</p>
<p>While risks remain, the long-term potential of decentralized finance continues attracting global attention.</p>
<p>Those who approach crypto with patience, research, and discipline often find themselves better prepared for future financial systems.</p>
</div>

<div class="conclusion">
<h2>Final Thoughts</h2>
<p>Crypto is not a get-rich-quick scheme — it is a dynamic financial ecosystem full of opportunity for those willing to learn and adapt.</p>
<p>Success requires strategy, patience, and strong risk management. With consistent effort and smart decision-making, digital assets can become a powerful wealth-building tool in 2026 and beyond.</p>
<p>Start small. Stay disciplined. Think long-term.</p>
</div>

</div>

<div id="verifyBox" style="display:none; margin:16px;">
<button class="btn" onclick="verifyNow()">Unlock Premium Crypto Guide</button>
</div>

<div id="continueBox" style="display:none; margin:16px;">
<a href="{BASE_URL}/r/{{redirect}}/{{slug}}">
<button class="btn">Continue to Investment Portal</button>
</a>
</div>

</body>
</html>
    """

# ================= REDIRECT =================
@app.get("/r/{{redirect}}/{{slug}}")
async def redirect_page(redirect: str, slug: str):
    funnel = await get_by_redirect(redirect, slug)
    if not funnel:
        return HTMLResponse("Invalid Link", status_code=403)
    return RedirectResponse(funnel[1])