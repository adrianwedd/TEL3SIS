# TEL3SIS – Telephony‑Linked Embedded LLM System ![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)

> **Codename:** TEL3SIS  
> A real‑time, voice‑first, agentic platform built on top of **vocode‑python** to answer incoming phone calls, hold natural LLM‑powered conversations, use external tools (Google Calendar, Weather, SMS, Email), record & transcribe audio, and hand off to a human seamlessly.

---

## ✨ Key Features

| Capability | Status | Notes |
|------------|--------|-------|
| Real‑time STT ↔️ LLM ↔️ TTS loop | ✅ Phase 1 | Whisper / Deepgram + GPT‑4o + ElevenLabs |
| Call recording & transcription | ✅ Phase 1 | Audio in `recordings/audio`, transcripts in `recordings/transcripts` |
| Toolchain via OpenAI Function Calling | 🔄 Phase 2 | Weather, Google Calendar, SMS/email |
| Context‑aware call forwarding | 🔄 Phase 3 | Whisper summary piped to human |
| Tri‑layer memory (Redis + SQLite + Vectors) | 🔄 Phase 4 | Session ↔ Mid‑term ↔ Long‑term |
| Safety oracle (pre‑execution) | 🔄 Phase 5 | Red‑team simulation + audit logs |
| Dashboard / metrics | 🛠 Phase 6 | Prometheus + Grafana |
| CI / CD & DevSecOps | 🛠 Continuous | Git‑secrets, pytest, pre‑commit |

---

## 🏗️ High‑Level Architecture

```
Caller
  │
  ▼        ┌──────────────────────┐
Twilio ►──►│  Flask Telephony API │◄───┐
           └──────────────────────┘    │  (async via Celery)
              │      ▲                 │
              │      │                 │
              ▼      │                 │
     ┌──────────────────────────────┐  │
     │  Vocode Streaming Pipeline   │  │
     │   • STT (Whisper/Deepgram)   │  │
     │   • LLM (OpenAI / Local)     │  │
     │      │                       │  │
     │      ▼                       │  │
     │   • Safety Oracle Filter     │  │
     │   • TTS (ElevenLabs)         │  │
     └──────────────────────────────┘  │
              │      ▲                 │
              ▼      │                 │
     ┌──────────────────────────────┐  │
     │      Tool Executor           │  │
     │  (function‑calling ➜ APIs)   │  │
     └──────────────────────────────┘  │
              │                        │
              ▼                        │
     ┌──────────────────────────────┐  │
     │   StateManager (Redis)       │  │
     ├──────────────────────────────┤  │
     │  TokenStore (SQLite, enc)    │  │
     │  Vector Memory (pgvector)    │  │
     └──────────────────────────────┘  │
              ▼                        │
      ┌──────────────────────────┐     │
      │   Celery Worker Pool     │─────┘
      └──────────────────────────┘
```

---

## 📂 Directory Layout (Phase 0 – 1)

```
TEL3SIS/
├── agents/               # Core & tool‑aware agent configs
├── server/
│   ├── app.py            # Flask entrypoint
│   ├── celery_app.py     # Celery factory
│   └── state_manager.py  # Redis wrapper
├── tools/                # Calendar, Weather, SMS, etc.
├── scripts/              # Dev helpers and startup tasks
├── tasks.yml             # Swarm task manifest
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🚀 Quick‑Start (Development)

**Prerequisites:** Git, Docker (+ Docker Compose), and [ngrok](https://ngrok.com) must be installed locally.

1. **Clone & enter repo**

   ```bash
   git clone https://github.com/yourname/TEL3SIS.git
   cd TEL3SIS
   ```

2. **Create `.env`**

   ```bash
   cp .env.example .env
   # ➜ populate Twilio, OpenAI, ElevenLabs, Deepgram, etc.
   ```

3. **Launch stack**

   ```bash
   docker compose up --build
   ```

4. **Expose to Twilio**

   ```bash
   ngrok http 3000
   # copy https URL ➜ Twilio Console ➜ Voice Webhook = https://xxxx.ngrok.io/inbound_call
   ```

5. **Call your Twilio number** – if TEL3SIS answers, Phase 1 is alive.

---
**Local (non‑Docker) setup**  
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server/app.py
```
> Use this only for lightweight debugging; Docker remains the canonical environment.

---

## ⚙️ Environment Variables

| Key | Description |
|-----|-------------|
| `BASE_URL` | Public URL for webhook (ngrok / k8s ingress) |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` | Telephony credentials |
| `OPENAI_API_KEY` | LLM access |
| `ELEVEN_LABS_API_KEY` | TTS voice |
| `REDIS_URL` | Redis connection for state & Celery broker |
| `CELERY_BROKER_URL` | Broker URL for Celery |
| `CELERY_RESULT_BACKEND` | Result backend for Celery |
| `DATABASE_URL` | SQLite / Postgres for mid‑term memory |
| `ESCALATION_PHONE_NUMBER` | Phone number used when handing off calls |
| `TOKEN_ENCRYPTION_KEY` | Base64 AES key for encrypting OAuth tokens |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth credentials for Calendar |
| `SENDGRID_API_KEY` | SendGrid API key for email notifications |
| `SENDGRID_FROM_EMAIL` | Sender email address for SendGrid |
| `NOTIFY_EMAIL` | Recipient for call transcripts |
| _see `.env.example`_ |

---

## 🛠️ Development Workflow

| Phase | Lead Tasks | Branch Tag |
|-------|------------|------------|
| **0 Init** | `INIT-00` → `INIT-04` | `init/` |
| **1 Core** | `CORE-01` → `CORE-06` + `OPS-01` | `core-mvp/` |
| **2 Tools** | `MEM-01`, `TOOL-01`–`05`, `OPS-02` | `tools/` |
| **3 Handoff** | `FWD-01`–`04` | `handoff/` |
| **4 Memory** | `MEM-02`, `MEM-03`, `QA-01` | `memory/` |
| **5 Safety** | `SAFE-01`–`03`, `SEC-01` | `safety/` |
| **6 UI/Ops** | `MON-01`, `UI-01`–`03` | `ui-ops/` |

Use feature branches named `<phase>/<task_id>-short-desc`, then open a PR referencing the task ID in **`tasks.yml`**.

---

## 🧪 Testing

```bash
pytest -q
```

* Unit tests live under `tests/`
* End‑to‑end call emulation via `scripts/dev_test_call.py`
* STT latency reduction via `scripts/warmup_whisper.py`

---

## 📊 Monitoring

* **Prometheus** scraps `/metrics`
* Example Grafana dashboard JSON under `ops/grafana/tel3sis.json`
* Alerts: STT/LLM/TTS > 3 s average latency → Slack

---

## 🔐 Security

* All secrets loaded from `.env` (never committed)
* `git-secrets` pre‑commit hook blocks accidental key leaks
* OAuth tokens are AES‑GCM encrypted via `cryptography` before storage
* Safety Oracle filters any risky LLM output before TTS

---

## 🖇️ Tool Plugins (Phase 2)

| Tool | Trigger Example | Implementation |
|------|-----------------|----------------|
| **Weather** | “What’s the weather tomorrow?” | OpenWeatherMap REST |
| **Calendar** | “Book a meeting at 10 AM” | Google Calendar API + OAuth |
| **SMS/Email** | “Text me the transcript” | Twilio Messages / SendGrid |

_Add new tool by implementing `tools/<name>.py` and registering JSON schema in `agents/tools_registry.py`._

### Notifications

Transcripts can be sent automatically once SendGrid and Twilio credentials are configured. Set:

- `SENDGRID_API_KEY` and `SENDGRID_FROM_EMAIL` – enables `send_email()`
- `NOTIFY_EMAIL` – default email recipient
- `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` – enables `send_sms()`

If these variables are unset, the system logs a warning and skips the notification.

---

## 🤝 Contributing

1. Fork & clone
2. Check open issues in **`tasks.yml`**
3. Branch ➜ code ➜ `pytest` ➜ PR
4. PR must pass CI + receive one approval
5. Install the hooks described in [CONTRIBUTING.md](CONTRIBUTING.md)

We follow the **Conventional Commits** spec.

---

## 📜 License

MIT. See `LICENSE`.

---

> Crafted with ♥ by **Adrian Wedd** & the TEL3SIS Swarm. Contributions welcome!