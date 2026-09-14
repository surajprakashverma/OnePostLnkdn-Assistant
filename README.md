#  OnePostLnkdn Assistant

An AI-powered, human-in-the-loop content pipeline that turns a personal learning roadmap into daily LinkedIn posts. It plans topics from your uploaded roadmap, drafts posts with Gemini, verifies quality automatically, sends you an approval email, and publishes to LinkedIn on its own — no manual writing or copy-pasting required.

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-black.svg)
![LLM](https://img.shields.io/badge/LLM-Gemini%202.5-purple.svg)
![Database](https://img.shields.io/badge/Database-PostgreSQL%20(Neon)-336791.svg)
![Deployed on Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🌐 Live Demo

**🚀 Try it live:** https://onepostlnkdn-web.onrender.com/login

> _Note: The free-tier Render instance may take ~30-60 seconds to wake up on first visit._

---

## ✨ Features

### 🗺️ Roadmap Ingestion
- Upload a learning roadmap as **PDF, DOCX, or TXT**.
- Choose how many days to spread it across.
- Gemini automatically structures the raw content into daily topics, subtopics, and short learning notes.
- Only one roadmap campaign can run at a time, preventing accidental duplicate runs.

### 🧠 AI Content Pipeline
- **Planner Agent** picks the next eligible topic, skipping anything already posted and retrying anything that was auto-rejected.
- **Generator Agent** drafts a natural, personal-sounding LinkedIn post using Gemini, free of Markdown formatting or placeholder text.
- **Verifier Agent** runs two layers of QA: rule-based checks (length, hashtag count, no leaked API keys/secrets, no Markdown) and an LLM critic that scores authenticity, relevance, and engagement quality.
- A **scored retry loop** automatically regenerates the draft with specific feedback if it fails QA, up to a configurable number of attempts.

### ✅ Human-in-the-Loop Approval
- Every draft is emailed to you with styled, clickable **Approve** and **Reject** buttons.
- Approval links are signed, single-use, time-limited JWT tokens.
- If you do not respond within a configurable window, the post is automatically rejected and the same topic is retried on the next cycle instead of being skipped.

### 📤 Automated LinkedIn Publishing
- Approved posts are automatically published to your LinkedIn profile via the LinkedIn Posts API.
- No manual copy-paste — the entire flow from roadmap upload to a live LinkedIn post is hands-off after your one-time approval click.

### 💬 Chat Dashboard
- Login-protected, single-page chat interface (no page scrollbars).
- Commands: `status`, `stop`, `trigger now`, plus a file upload panel for starting a new roadmap.
- Real-time feedback on roadmap progress: days posted, pending approval, and the next topic in line.

### ☁️ Deployment
- Ready for **Render deployment** with a persistent web service plus scheduled cron jobs.
- Uses **PostgreSQL (Neon)** for persistent storage across deploys.
- Includes `requirements.txt` and `render.yaml` for one-click infrastructure setup.

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Backend** | Python 3.13, FastAPI, Uvicorn |
| **LLM** | Google Gemini (via LangChain) |
| **Database** | PostgreSQL (Neon, free tier), SQLAlchemy ORM |
| **Email** | Resend (HTTPS API) |
| **Scheduling** | APScheduler (local), Render Cron Jobs (production) |
| **Auth** | Signed JWT tokens (dashboard session + single-use approval links) |
| **File parsing** | pypdf, python-docx |
| **Deployment** | Render (Web Service + Cron Jobs) |
| **Version Control** | Git, GitHub |

---

## 📸 Screenshots

> _Add screenshots after deployment._

- 🔐 **Login Page** — Branded, gradient-styled sign-in screen
- 💬 **Chat Dashboard** — Status, stop, trigger now, and roadmap upload in one screen
- 📧 **Approval Email** — Draft preview with Approve / Reject buttons
- 📤 **Published Post** — Example of an auto-published LinkedIn post

---

## 📁 Project Structure

```
OnePostLnkdnAssistant/
│
├── app/
│   ├── agents/
│   │   ├── planner.py            # Picks next eligible topic (duplicate-check aware)
│   │   ├── generator.py          # Drafts posts via Gemini
│   │   ├── verifier.py           # Rule-based + LLM critic QA, scored retry loop
│   │   ├── pipeline.py           # Orchestrates planner -> generator -> verifier -> email
│   │   └── linkedin_poster.py    # Publishes approved posts to LinkedIn
│   │
│   ├── api/
│   │   ├── approval_routes.py    # /approve and /reject webhook endpoints
│   │   ├── auth_routes.py        # LinkedIn OAuth login/callback
│   │   ├── user_auth_routes.py   # Dashboard login/logout
│   │   ├── pipeline_routes.py    # Manual pipeline trigger endpoint
│   │   └── dashboard_routes.py   # Chat dashboard UI and commands
│   │
│   ├── core/
│   │   ├── config.py             # Centralized settings from .env
│   │   └── time_utils.py         # Timezone-safe datetime helpers
│   │
│   ├── db/
│   │   ├── database.py           # SQLAlchemy engine/session setup
│   │   └── models.py             # RoadmapTopic, PostedLog, RoadmapRun
│   │
│   ├── services/
│   │   ├── email_service.py      # Sends approval emails via Resend
│   │   ├── token_service.py      # Signs/verifies approval JWTs
│   │   ├── auth_service.py       # Dashboard login/session handling
│   │   ├── roadmap_ingest_service.py   # PDF/DOCX/TXT text extraction + Gemini structuring
│   │   ├── roadmap_run_service.py      # Start/stop/status of roadmap campaigns
│   │   └── scheduler_jobs.py     # Auto-reject expired approvals
│   │
│   ├── scheduler.py              # APScheduler wiring (local use only)
│   └── main.py                   # FastAPI application entrypoint
│
├── data/
│   └── uploads/                  # Temporary storage for uploaded roadmap files
│
├── render.yaml                   # Render deployment configuration
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
└── README.md                     # Project documentation
```

---

## 🚀 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/surajprakashverma/OnePostLnkdnAssistant.git
cd OnePostLnkdnAssistant
```

### 2. Create a virtual environment (recommended)
```bash
# Windows
python -m venv myvenv
myvenv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv myvenv
source myvenv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and fill in real values (Gemini API key, Resend API key, LinkedIn OAuth credentials, Neon database URL, admin login, JWT secret, schedule times).

### 5. Run the app
```bash
python -m uvicorn app.main:app --reload
```

### 6. Open your browser
Visit **http://localhost:8000/login**

---

## 💡 Usage

### 🗺️ Starting a new roadmap

1. Log in to the dashboard.
2. Choose a roadmap file (PDF, DOCX, or TXT) in the upload panel.
3. Set the number of days to spread it across.
4. Click **Upload & Start** — Gemini structures the roadmap and the campaign begins.

### 💬 Managing an active roadmap

Type any of these commands in the chat box:

| Command | What it does |
|---|---|
| `status` | Shows the active roadmap's filename, start date, posts completed, pending approvals, and the next topic in line |
| `stop` | Stops the current roadmap campaign so a new one can be started |
| `trigger now` | Manually runs today's post generation immediately, instead of waiting for the scheduled time |

### 📧 Approving a post

1. Check your inbox for an email titled `[PASS] LinkedIn Post Ready for Review` (or `[REVIEW]` if it did not meet the automatic quality threshold).
2. Read the drafted post in the email body.
3. Click **Approve and Post** to publish it, or **Reject** to discard it (the same topic will be retried on the next scheduled cycle).

---

## ⚙️ How It Works

1. **Roadmap upload** — the file is parsed (pypdf / python-docx), sent to Gemini, and structured into N days of topics, then saved to the database and the original file is deleted.
2. **Scheduled trigger** — once daily, the Planner Agent selects the next eligible topic from the active roadmap, skipping already-posted or recently-attempted topics.
3. **Generation and verification** — the Generator Agent drafts a post, and the Verifier Agent checks it against rule-based criteria and an LLM critic score, retrying with feedback if it fails.
4. **Approval email** — the best draft is saved with a signed, single-use approval token and emailed to you with Approve / Reject buttons.
5. **Auto-reject on timeout** — a background job checks every 15 minutes for drafts past their approval deadline and marks them as auto-rejected, making the same topic eligible again on the next cycle.
6. **Auto-publish** — a background job checks every 2 minutes for approved drafts and publishes them to LinkedIn via the Posts API, recording the returned post URN.

---

## ☁️ Deployment on Render

This app deploys as **one web service plus three cron jobs**, all defined in `render.yaml`.

### Prerequisites in repo root
- `requirements.txt`
- `render.yaml`
- `app/main.py` (FastAPI entrypoint)

### Steps
1. Push code to GitHub.
2. Create a free PostgreSQL database on [Neon](https://neon.tech) and copy its connection string.
3. Go to [render.com](https://render.com) → create a Render **Environment Group** containing all variables from `.env.example` (with real values, including the Neon `DATABASE_URL`, and `ENABLE_INPROCESS_SCHEDULER=false`).
4. Go to **New +** → **Blueprint**, connect your GitHub repo, and Render will read `render.yaml` to provision:
   - `onepostlnkdn-web` — the dashboard, login, and approval webhook (Free plan)
   - `daily-pipeline-trigger` — runs once daily
   - `auto-reject-check` — runs every 15 minutes
   - `publish-approved-check` — runs every 2 minutes
5. Update your LinkedIn Developer App's authorized redirect URL to match your live Render URL.
6. Visit `https://your-app.onrender.com/auth/linkedin/login` once to authorize LinkedIn and obtain a production access token.

### Auto-deploy
Every `git push` to `main` triggers an automatic redeploy of the web service and all cron jobs.

---

## 👥 Who Is This For?

- 📚 **Self-learners** documenting a structured learning journey (e.g., "100 Days of Code") who want consistent LinkedIn visibility without daily writing effort.
- 🧑‍💻 **Developers and engineers** building a personal brand while learning a new stack.
- 🎯 **Anyone practicing "learning in public"** who wants an AI co-pilot that plans, drafts, and verifies content, while keeping a human approval step in the loop.

---

## ⚠️ Disclaimer

> This tool posts to your real LinkedIn profile on your behalf, only after your explicit approval via email.
> Always review each drafted post carefully before approving, especially posts flagged as not meeting the automatic quality threshold.
> The author is not responsible for content published as a result of approvals granted through this tool.

---

## 👨‍💻 Author

**Suraj Prakash Verma**
- 🏢 UST
- 🌐 GitHub: https://github.com/surajprakashverma

---

## 📄 License

This project is licensed under the **MIT License** — see the LICENSE file for details.

---

## 🌟 Show Your Support

If you found this project useful, give it a ⭐ on GitHub!

Contributions, issues, and feature requests are always welcome. 🙌
