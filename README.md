
# AutoResQ – Incident Copilot (Hackathon Demo)

This repo gives you a **complete, demo-ready setup** to show an end‑to‑end incident flow:

**PagerDuty/Test webhook → Flask receiver → AI suggestion (stub) → SQLite → Streamlit dashboard → (optional) mock automation**

Works great with **Cloudflare Tunnel (`cloudflared`)** for a public URL without VPN issues.

---

## 🧩 Structure
```
autoresq_demo/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ webhook_receiver.py      # Flask endpoint: /pd-webhook
├─ db.py                    # tiny SQLite helper
├─ streamlit_app.py         # live dashboard
├─ gradio_live_demo.py      # optional public UI with gradio.live
├─ scripts/
│  ├─ run_cloudflared.txt   # copy-paste command
│  └─ test_post.sh          # curl to send sample
├─ sample_payloads/
│  ├─ ping.json
│  ├─ queue_depth.json
│  └─ db_timeout.json
└─ sop_docs/                # put your SOPs here (text/markdown/pdf)
```

---

## ⚙️ Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# copy env
cp .env .env
# edit .env if you want to change WEBHOOK_SECRET etc.
```

---

## 🚇 Public URL (recommended): Cloudflare Tunnel

Install:
```bash
brew install cloudflared
```

Run your Flask receiver:
```bash
export FLASK_DEBUG=1
python alert_webhook_handler.py
```

Start tunnel in another terminal:
```bash
cloudflared tunnel --url http://localhost:5000
```
Use the printed `https://*.trycloudflare.com/pd-webhook` as your webhook URL.

> You can also simulate from your machine using `scripts/test_post.sh`.

---

## 🧪 Send a test alert

**Option A – cURL (local or tunnel):**
```bash
bash scripts/test_post.sh https://YOUR_PUBLIC_OR_LOCAL_URL/pd-webhook
```

**Option B – paste JSON into Streamlit "Manual Inject":**
```bash
streamlit run dashboard_app.py
```

---

## 📊 Streamlit Dashboard

Run:
```bash
streamlit run dashboard_app.py
```
Features:
- Live table of events (latest first)
- Detail view with the AI suggestion (stub)
- Buttons to **Approve/Run Fix** (mock) and **Resolve**
- Manual inject box for quick demos

---

## 🧠 AI / RAG integration (optional)

Inside `webhook_receiver.py` there is a stub `generate_ai_plan()`.
Replace it with calls to Bedrock/Claude or a simple RAG over `sop_docs/`.
To keep the demo light, this repo ships without FAISS. You can still:
- load `.md` or `.txt` from `sop_docs/`
- do simple keyword match to select relevant snippets
- feed them to your LLM (if you enable Bedrock/OpenAI)

---

## 🔐 Safety Notes
- Use **sanitized test payloads** only.
- Keep WEBHOOK_SECRET set; PD or your curl must send `X-Webhook-Token` header.
- Mock automation only; never hit prod from the demo.

Good luck & have fun! – AutoResQ 🚀
