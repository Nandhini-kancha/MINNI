# Minni 🌸 - AI Safety Assistant Chatbot API

**Minni** is a friendly, supportive, age-appropriate AI safety assistant Python FastAPI chatbot API powered by **Google Gemini**. Minni is designed specifically to help **children and women** navigate body safety, personal space, stranger safety, bullying, online privacy, and unsafe situations in a gentle, empowering, and non-judgmental way.

---

## 🌟 Key Features

- **🛡️ Pre-Generation Safety Layer**: Analyzes user input intent and assesses risk levels (`SAFE`, `SENSITIVE`, `HIGH_RISK`) before generating responses.
- **🚨 Immediate Emergency Interception**: High-risk situations (active abuse, violence, immediate danger, self-harm) bypass LLM generation to immediately return pre-defined, supportive safe responses with official helpline numbers (**1098 Childline**, **181 Women Helpline**, **112/911 Emergency Services**).
- **🤖 Powered by Google Gemini**: Leverages Google Gemini for natural, warm, conversational, age-appropriate guidance in English, Telugu, and Romanized Teluglish.
- **🔒 Privacy First & No Secrets Principle**:
  - Never collects unnecessary personal information (full names, addresses, phone numbers).
  - Emphasizes that secrets about touching or safety are **never okay** to keep and encourages speaking to a trusted adult.
- **💬 Session Context**: Tracks multi-turn conversation history per `session_id`.
- **🤖 Robot Ready API**: Pure, lightweight REST interface (`POST /api/chat`) tailored for speech-to-text / text-to-speech robot integration (`"Hey Minni"` ➔ STT ➔ `POST /api/chat` ➔ TTS ➔ Robot Speaks).
- **📚 Interactive OpenAPI / Swagger Docs**: Available out-of-the-box via FastAPI at `/docs` and `/redoc`.

---

## 📁 Project Structure

```
minni/
├── Dockerfile                   # Production Docker container setup
├── Procfile                     # Process configuration for Railway / Heroku
├── render.yaml                  # Render.com automatic deployment blueprint
├── app/
│   ├── main.py                  # FastAPI entry point & CORS configuration
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
└── README.md                    # Project documentation
```

---

## 🚀 Running the Server Locally

### 1. Setup Environment
```bash
cd minni
python -m venv venv

# Windows
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key
Copy `.env.example` to `.env` and set your `GEMINI_API_KEY`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
```

### 3. Start Uvicorn Server
```bash
uvicorn app.main:app --reload
```

- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Chat Endpoint**: `POST /api/chat`
- **Health Endpoint**: `GET /api/health`

---

## 📡 API Usage Example

### `POST /api/chat`

**Request Payload:**
```json
{
  "message": "What is good touch and bad touch?",
  "session_id": "session-child-101",
  "audience": "child"
}
```

**Response Payload (`200 OK`):**
```json
{
  "response": "Hi there! Remember, your body belongs to YOU and you have the right to feel safe all the time...\n\nIf anyone ever tries to touch your private parts:\n1. Say NO!\n2. GO AWAY / RUN to a safe place.\n3. TELL a trusted adult immediately!",
  "session_id": "session-child-101",
  "intent": "body_safety",
  "risk_level": "SENSITIVE",
  "flagged": false,
  "action_taken": "normal_response",
  "helpline_info": null
}
```

---

## 🤖 Robot Integration Flow

```
                      +-------------------+
                      |   "Hey Minni!"    |
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      | Speech-To-Text    |
                      +---------+---------+
                                |
                                v (HTTP POST /api/chat)
                      +-------------------+
                      |   Minni FastAPI   |
                      |   Backend API     |
                      +---------+---------+
                                |
                                v (JSON Response)
                      +-------------------+
                      | Text-To-Speech    |
                      +---------+---------+
                                |
                                v
                      +-------------------+
                      | Robot Speaks Text |
                      +-------------------+
```

---

## 🧪 Running Automated Tests

```bash
$env:PATH="c:\Users\Nandhini\OneDrive\Desktop\minni\venv\Scripts;" + $env:PATH; python -m pytest
```
