# LegalGPT

LegalGPT is a legal document intelligence workspace with upload analysis, clause extraction, risk flagging, retrieval-based Q&A, document comparison, template generation, and report export.

## Run

This workspace has a disk limit, so the runnable server uses only the Python standard library:

```bash
APP_PORT=8010 python3 server.py
```

Open:

```txt
http://127.0.0.1:8010
```

## Run In VS Code

1. Open this project folder in VS Code.
2. Open `.env.example` and copy the Groq values into your shell environment if you want live AI responses.
3. Press `Cmd+Shift+B` and choose `Run LegalGPT`, or open the Run panel and start `Run LegalGPT`.
4. Open `http://127.0.0.1:8010` in your browser.

## Groq

Set `GROQ_API_KEY` to enable live Groq analysis and answers:

```bash
export GROQ_API_KEY=your_groq_api_key_here
export GROQ_MODEL=llama-3.1-70b-versatile
APP_PORT=8010 python3 server.py
```

Without `GROQ_API_KEY`, the app still runs with local heuristic analysis and retrieval-only chat responses.

## Upload Support

The zero-dependency runner supports `.txt` and `.md` uploads. The FastAPI architecture and optional parser modules are included for PDF/DOCX support, but installing those packages exceeded this workspace's disk allowance.

## Project Layout

- `server.py` - zero-dependency runnable web/API server
- `legalgpt_frontend/` - static app UI
- `legalgpt_backend/` - FastAPI-style backend architecture and services
- `outputs/legalgpt-groq-build-prompt.md` - Groq-specific build prompt
