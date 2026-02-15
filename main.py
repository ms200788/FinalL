import os
import secrets
import string
import asyncio
import urllib.parse
import urllib.request
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
funnels = {}  # slug -> (redirect, link)
lock = asyncio.Lock()  # concurrency lock

# ================= LOAD DATA FROM TXT =================
if os.path.exists(TXT_FILE):
    with open(TXT_FILE, "r") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) == 3:
                slug, redirect, link = parts
                funnels[slug] = (redirect, link)

# ================= UTILITY FUNCTIONS =================
def generate_slug():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

def generate_redirect():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))

async def save_funnel(slug, redirect, link):
    """Save funnel to memory and append to TXT safely."""
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
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=data, timeout=10)
    except:
        pass

async def send_to_channel(text):
    if not BOT_TOKEN or not CHANNEL_ID:
        return
    data = urllib.parse.urlencode({"chat_id": CHANNEL_ID, "text": text}).encode()
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=data, timeout=10)
    except:
        pass

# ================= USER ROUTES =================
@app.get("/{slug}", response_class=HTMLResponse)
async def user_page(slug: str):
    funnel = await get_by_slug(slug)
    if not funnel:
        return HTMLResponse("Page Not Found", status_code=404)

    redirect = funnel[0]

    return f"""
    <!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Boost Your Dating Life</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{ font-family: Arial; line-height:1.8; margin:0; background:#0f2027; color:#eaeaea; }}
h1,h2,h3,h4 {{ color:#4da3ff; }}
.section {{ background:#fff; padding:25px; margin-bottom:30px; border-left:6px solid #4da3ff; }}
.card {{ background:#fff; color:#000; border-radius:16px; padding:20px; margin:16px; }}
.btn {{ background:#fff; color:#4da3ff; border:none; padding:14px; width:100%; border-radius:30px; font-size:16px; cursor:pointer; }}
.timer {{ text-align:center; font-size:16px; margin:20px 0; }}
.conclusion {{ background:#f0f3ff; padding:20px; border-left:5px solid #4a63ff; border-radius:12px; }}
.topbar {{background:#121212; color:#fff; padding:12px 16px; font-size:20px; font-weight:700; }}
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
            document.getElementById("timerText").innerText="Please verify to continue";
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
    window.open("{BASE_URL}/go/NVDOEC","_blank");
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
<div class="topbar">Boost Your Dating Life</div>
<div class="card">
<h1>Boost Your Dating Life & Attraction Skills</h1>
<div class="timer">
<p id="timerText">Please wait <b id="t">20</b> seconds while content loads</p>
</div>

<div class="section">
<h2>Introduction</h2>
<p>Modern dating can be challenging, whether online or offline. Everyone wants to feel confident and attractive. With a few simple strategies, you can boost your charm, make meaningful connections, and improve your dating life. In this guide, we will explore actionable tips, communication strategies, body language techniques, and practical advice that can help you succeed in both casual and serious dating environments.</p>
</div>

<div class="section">
<h2>Enhance Your Confidence</h2>
<p>Confidence is one of the most attractive traits a person can have. It can make a huge difference in your interactions. Confidence comes from a combination of self-awareness, self-care, and mental attitude. Work on self-improvement through fitness, grooming, and positive thinking. Small habits like maintaining good posture, making eye contact, and smiling genuinely can dramatically improve your appeal. Over time, this confidence becomes natural and helps you navigate dating situations with ease.</p>
<p>Start by setting small goals each day, such as talking to one new person, complimenting someone genuinely, or initiating a short conversation online. Each success, no matter how small, builds your self-esteem.</p>
</div>

<div class="section">
<h2>Mastering Conversation Skills</h2>
<p>Good conversations are the backbone of dating. They show that you are interested, attentive, and thoughtful. Start with open-ended questions to keep the dialogue flowing. Avoid simple yes/no questions. For example, ask "What was the most memorable trip you’ve ever taken?" instead of "Do you like traveling?" This encourages your date to share experiences and feelings, making the interaction more engaging.</p>
<p>Listening is equally important. People are naturally drawn to those who genuinely listen and respond thoughtfully. Practice active listening by summarizing what the other person says and asking follow-up questions. This makes your conversations deeper and more meaningful.</p>
<ul>
<li>Ask unique and memorable questions.</li>
<li>Share small personal stories to create a connection.</li>
<li>Use humor to lighten the conversation and show personality.</li>
<li>Be curious, but avoid being intrusive.</li>
</ul>
</div>

<div class="section">
<h2>Body Language & Non-Verbal Communication</h2>
<p>Non-verbal cues play a massive role in attraction. Subtle things like standing tall, keeping your shoulders relaxed, and making appropriate eye contact can make you seem more approachable and confident. Avoid closed body language such as crossed arms or looking away frequently, as these can give off disinterest or insecurity.</p>
<ul>
<li>Smile genuinely to signal warmth and friendliness.</li>
<li>Mirror the other person's gestures subtly to create subconscious rapport.</li>
<li>Use open gestures to show you are receptive and engaged.</li>
<li>Maintain personal space, respecting boundaries.</li>
</ul>
<p>Small changes in body language can transform how others perceive you and improve your dating outcomes.</p>
</div>

<div class="section">
<h2>Using Online Dating Apps Effectively</h2>
<p>Online dating apps are a great way to meet people, but standing out is key. Optimize your profile with high-quality photos that showcase your personality. Include a short, witty bio that reflects your interests. Respond thoughtfully to messages instead of using generic replies; personalized messages increase the chances of meaningful connections.</p>
<p>Focus on quality over quantity. Swiping endlessly may waste time, whereas engaging genuinely with a few profiles yields better results. Utilize app features such as prompts, badges, and verification for credibility and trust-building.</p>
</div>

<div class="section">
<h2>Self-Improvement Hacks</h2>
<p>Personal growth enhances your dating prospects naturally. Being well-rounded makes you interesting and confident. Here are practical ways to improve yourself:</p>
<ul>
<li>Exercise regularly to improve energy, posture, and confidence.</li>
<li>Practice mindfulness and meditation to stay calm and handle rejection gracefully.</li>
<li>Read books or take online courses to learn new skills and hobbies.</li>
<li>Develop social intelligence by observing and analyzing interactions.</li>
<li>Set personal goals in fitness, career, and social life to create a sense of achievement.</li>
</ul>
</div>

<div class="section">
<h2>Fashion & Grooming Tips</h2>
<p>Appearance is important, but style is about expressing yourself authentically. Dress in a way that makes you feel confident and suits your personality. Pay attention to grooming, including hair, nails, and hygiene. Small details like clean shoes or matching accessories make a lasting impression.</p>
<p>Color coordination, wearing clothes that fit well, and subtle scents contribute to attractiveness. Avoid overcomplicating your style; simplicity and cleanliness often leave the strongest impact.</p>
</div>

<div class="section">
<h2>Boost Your Online Presence</h2>
<p>In the digital age, your online presence can greatly influence your dating success. Social media profiles reflect your personality and interests. Post authentic content, avoid excessive negativity, and showcase hobbies or travel experiences. This creates conversation starters and shows that you lead an interesting life.</p>
<p>Maintain balance and avoid over-sharing; subtlety is appealing. Your online presence should complement your real-life personality rather than create a false impression.</p>
</div>

<div class="section">
<h2>Dating Etiquette & Respect</h2>
<p>Respect and courtesy are timeless traits that attract others. Always be punctual, honest, and considerate. Listen attentively and avoid interrupting. Consent and personal boundaries should always be honored, whether in online interactions or in-person meetings.</p>
<p>Being respectful builds trust and rapport, creating a foundation for deeper connections. Simple gestures like thanking someone for their time, complimenting sincerely, and following up appropriately leave a lasting positive impression.</p>
</div>

<div class="section">
<h2>Planning Memorable Dates</h2>
<p>Memorable dates help deepen connections. Instead of generic coffee or dinner, plan activities that spark fun, laughter, and shared experiences. Outdoor adventures, workshops, or interactive events give opportunities for genuine bonding. Consider the other person's interests and preferences while planning. Being thoughtful and creative in planning shows attentiveness and care.</p>
</div>

<div class="section">
<h2>Conclusion</h2>
<p>Improving your dating life is a journey of self-confidence, communication, and personal growth. By consistently applying these strategies—confidence building, effective communication, body language mastery, online optimization, personal grooming, and thoughtful dating—you can attract meaningful connections. Start small, remain authentic, and approach dating as a fun and educational experience.</p>
<p>Remember, the key to success is balance: be interesting, confident, and respectful. Over time, these habits will naturally improve your dating outcomes and social life. Take action today and watch your confidence and appeal grow exponentially!</p>
</div>

</div>

<div id="verifyBox" style="display:none; margin:16px;">
<button class="btn" onclick="verifyNow()">Verify to Continue</button>
</div>
<div id="continueBox" style="display:none; margin:16px;">
<a href="{BASE_URL}/{redirect}/{slug}">
<button class="btn">Continue</button>
</a>
</div>
</body>
</html>
    """

@app.get("/{redirect}/{slug}")
async def redirect_page(redirect: str, slug: str):
    funnel = await get_by_redirect(redirect, slug)
    if not funnel:
        return HTMLResponse("Invalid Link", status_code=403)
    return RedirectResponse(funnel[1])

# ================= TELEGRAM WEBHOOK =================
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

        # generate unique slug
        for _ in range(10):
            slug = generate_slug()
            if slug not in funnels:
                break
        else:
            await send_message(chat_id, "Failed to generate slug.")
            return {"ok": True}

        redirect = generate_redirect()
        await save_funnel(slug, redirect, link)

        # Send backup to channel
        await send_to_channel(f"{slug}|{redirect}|{link}")

        await send_message(chat_id, f"User URL:\n{BASE_URL}/{slug}")
        await send_message(chat_id, f"Redirect URL:\n{BASE_URL}/{redirect}/{slug}")

    return {"ok": True}