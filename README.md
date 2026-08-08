# Minni 🌸 - AI Safety Companion (Web & API)

**Minni** is a friendly, supportive, age-appropriate AI safety companion API & Web Application built with **FastAPI**, **Google Gemini**, and a **Rich Web UI**. Minni is designed specifically to help **children and women** navigate body safety, personal space, stranger safety, bullying, online privacy, and unsafe situations in a gentle, empowering, and non-judgmental way.

---

## 🌟 Key Features

- **🌐 Rich Web Chat UI**: Built with glassmorphism aesthetics, responsive layouts, mode switches (Child / Woman / General), and safety prompt chips.
- **🎙️ Voice Input & Output**: Built-in Speech-to-Text (Voice Mic input) and Text-to-Speech (Minni speaking answers aloud) via Web Speech API.
- **🛡️ Pre-Generation Safety Layer**: Analyzes user input intent and assesses risk levels (`SAFE`, `SENSITIVE`, `HIGH_RISK`) before generating responses.
- **🚨 Immediate Emergency Interception**: High-risk situations (active abuse, violence, immediate danger, self-harm) bypass LLM generation to immediately return pre-defined, supportive safe responses with official helpline numbers (**1098 Childline**, **181 Women Helpline**, **112/911 Emergency Services**).
- **🤖 Powered by Google Gemini**: Leverages Google Gemini for natural, warm, conversational, age-appropriate guidance.
- **☁️ Netlify & Cloud Ready**: Complete deployment configuration (`netlify.toml`, `mangum` adapter, `Dockerfile`, `render.yaml`).

---

## 📁 Project Structure

```
minni/
├── netlify.toml                 # Netlify build and serverless function configuration
├── netlify/
│   └── functions/
│       └── api.py               # Mangum handler for Netlify Serverless Functions
├── Dockerfile                   # Production Docker container setup
├── Procfile                     # Process configuration for Railway / Heroku
├── render.yaml                  # Render.com automatic deployment blueprint
├── app/
│   ├── main.py                  # FastAPI entry point, CORS & static files serving
│   ├── static/                  # Web Chat UI Assets
│   │   ├── index.html           # Main Web UI markup
│   │   ├── css/styles.css       # Glassmorphism design system
│   │   └── js/app.js            # Chat UI logic, TTS, STT, session manager
│   ├── core/
│   │   ├── config.py            # Settings & environment variables
│   │   └── system_prompts.py    # Minni persona & safety principles
│   ├── services/
│   │   ├── safety_service.py    # Safety classification & emergency overrides
│   │   ├── gemini_service.py    # Gemini API client & rule-based fallback
│   │   └── session_service.py   # In-memory session context manager
│   ├── schemas/
│   │   └── chat.py              # Pydantic request & response schemas
│   └── api/
│       ├── router.py            # API route aggregator
│       └── v1/
│           ├── chat.py          # POST /api/chat endpoint
│           └── health.py        # GET /api/health endpoint
├── tests/
│   ├── test_health.py           # Health check tests
│   ├── test_safety.py           # Safety classification unit tests
│   └── test_chat.py             # Chat API integration tests
├── .env.example                 # Environment variables template
├── .env                         # Local environment file
├── requirements.txt             # Python dependencies
└── README.md                    # Documentation & deployment guide
```

---

## 🚀 Running Locally

```bash
cd minni

# Activate virtual environment
.\venv\Scripts\activate

# Start server
uvicorn app.main:app --reload
```

- **Live Web Chat UI**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Endpoint**: `GET /api/health`

---

## ☁️ Deploying on Netlify (Step-by-Step)

### Option 1: Deploying via Netlify CLI (Recommended for instant setup)

1. **Install Netlify CLI**:
   ```bash
   npm install -g netlify-cli
   ```

2. **Login to Netlify**:
   ```bash
   netlify login
   ```

3. **Deploy the Site**:
   ```bash
   netlify deploy --prod
   ```
   - When asked for publish directory: enter `app/static`
   - When asked for build command: enter `pip install -r requirements.txt`

4. **Add your Gemini API Key in Netlify Dashboard**:
   - Open your site dashboard on Netlify.
   - Go to **Site Configuration** ➔ **Environment variables**.
   - Add variable: `GEMINI_API_KEY` = `your_gemini_api_key_here`.

---

### Option 2: Deploying via GitHub & Netlify Dashboard

1. Push your `minni` project folder to GitHub.
2. Log into [Netlify](https://app.netlify.com/).
3. Click **Add new site** ➔ **Import an existing project** ➔ Select **GitHub**.
4. Select your `minni` repository.
5. Netlify will automatically detect `netlify.toml`.
6. Add `GEMINI_API_KEY` under **Environment variables**.
7. Click **Deploy Minni**! Your site will be live on `https://<your-site-name>.netlify.app`.

---

## 🐳 Alternative Deployment Options

- **Render**: Connect repository to Render. It will read `render.yaml` automatically.
- **Docker**:
  ```bash
  docker build -t minni-app .
  docker run -p 8000:8000 -e GEMINI_API_KEY="your_key" minni-app
  ```

---

## 🧪 Running Automated Tests

```bash
$env:PATH="c:\Users\Nandhini\OneDrive\Desktop\minni\venv\Scripts;" + $env:PATH; python -m pytest
```
