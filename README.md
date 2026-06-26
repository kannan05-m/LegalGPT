# ⚖️ LegalGPT — Legal Document Intelligence System

> An AI-powered legal workspace that lets users upload legal documents and interact with them through natural language — powered by RAG, Groq LLMs, and a FastAPI + React architecture.

---

## 🚀 Features

- 📄 **Document Upload & Analysis** — Upload `.txt`, `.md`, PDF, or DOCX legal files for instant parsing
- 🔍 **Clause Extraction** — Automatically identifies and surfaces key legal clauses
- ⚠️ **Risk Flagging** — Highlights potentially risky or ambiguous contract language
- 💬 **Retrieval-Augmented Q&A** — Ask questions about your document; get grounded, cited answers
- 📊 **Document Comparison** — Diff two documents to surface changed or missing clauses
- 📝 **Template Generation** — Generate standard legal document templates on demand
- 📤 **Report Export** — Export analysis results as structured reports

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq (`llama-3.1-70b-versatile`) |
| Backend | FastAPI + Python |
| Frontend | HTML / CSS / JavaScript (static) |
| RAG | Retrieval-based document Q&A |
| Server (zero-dep) | Python standard library (`server.py`) |

---

## 📁 Project Structure

```
LegalGPT/
├── server.py                  # Zero-dependency runnable server (stdlib only)
├── main.py                    # FastAPI entry point (full stack)
├── requirements.txt           # Optional full-stack dependencies
├── legalgpt_backend/          # FastAPI-style backend services & architecture
├── legalgpt_frontend/         # Static UI (HTML/CSS/JS)
├── .env.example               # Environment variable template
└── .gitignore
```

---

## ⚡ Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/kannan05-m/LegalGPT.git
cd LegalGPT
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Add your Groq API key to .env
```

`.env.example`:
```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile
```

### 3. Run (zero-dependency mode — no installs needed)

```bash
APP_PORT=8010 python3 server.py
```

Open → [http://127.0.0.1:8010](http://127.0.0.1:8010)

### 4. Run full FastAPI stack (optional)

```bash
pip install fastapi uvicorn python-multipart pydantic
uvicorn main:app --reload --port 8010
```

---

## 🤖 Groq Integration

Set `GROQ_API_KEY` to enable live LLM-powered analysis:

```bash
export GROQ_API_KEY=your_groq_api_key_here
export GROQ_MODEL=llama-3.1-70b-versatile
APP_PORT=8010 python3 server.py
```

Without a Groq key, the app runs in **offline mode** — local heuristic analysis and retrieval-only responses still work, no API calls required.

---

## 🖥️ VS Code Setup

1. Open the project folder in VS Code
2. Copy your Groq credentials into your shell environment (see above)
3. Press `Cmd+Shift+B` → select **Run LegalGPT**
4. Open [http://127.0.0.1:8010](http://127.0.0.1:8010)

---

## 🔒 Environment & Security

- Never commit your `.env` file — it's in `.gitignore`
- Use `.env.example` as a reference template with placeholder values only
- Get a free Groq API key at [console.groq.com](https://console.groq.com)

---

## 🗺️ Roadmap

- [ ] PDF and DOCX upload support (full parser integration)
- [ ] Vector store with FAISS for semantic document retrieval
- [ ] Multi-document RAG across a legal knowledge base
- [ ] Jurisdiction-aware clause risk scoring

---

## 👤 Author

**Kannan Mehra**  
B.Tech AI & ML — ADGIPS, GGSIPU  
[GitHub](https://github.com/kannan05-m)

---

## 📄 License

MIT
