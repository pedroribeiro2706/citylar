# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Citylar is an executive sales dashboard with an integrated AI consultant chatbot, built with Streamlit. It tracks employee "Ticket Médio" (average ticket) performance, displaying rankings, historical records, and evolution trends. The AI consultant connects to n8n workflows that query Google Sheets data.

## Commands

```bash
# Setup
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt

# Run
streamlit run app.py
# Serves at http://localhost:8501
```

## Architecture

**app.py** — Single-file Streamlit application (~366 lines) structured as:

1. **Session state setup** (UUID session IDs, message history, input deduplication)
2. **Custom CSS** (dark maroon theme, sidebar chat styling, Font Awesome icons)
3. **Sidebar** — Navigation menu + AI consultant chat panel with text input, audio recording (mic_recorder), voice toggle, and file upload (XLSX/CSV)
4. **Input processing** — Sends user text/audio to n8n webhooks, handles JSON and multipart responses, plays back TTS audio
5. **Data loading** — `carregar_dados()` with `@st.cache_data(ttl=60)`, fetches from API, parses R$ currency and dates
6. **Dashboard** — Period selector, results table with color-coded evolution (▲/▼), three Plotly charts (monthly ranking, records by year, individual 12-month trend)

**External API endpoints** (n8n webhooks at `https://workflows-mvp.clockdesign.com.br/webhook`):
- `/dados-dashboard` — GET, returns employee performance data
- `/chat` — POST, AI consultant chat processing
- `/citylar/upload` — POST, file upload handler

**Theme** defined in `.streamlit/config.toml`: dark background (#1f1f1f), maroon primary (#800020), white text.

## Key Conventions

- Language: Portuguese (BR) for all UI text, variable names, and function names (e.g., `carregar_dados`, `formatar_evolucao`, `truncar_nome`)
- Charts use Plotly with maroon (#800020) as primary color, no display mode bar
- Currency formatted as `R$ X,XX` (Brazilian Real)
- Dates parsed with `dayfirst=True` (DD/MM/YY format)
- n8n workflow JSON files in root are versioned by date (e.g., `Citylar - 14fev2026.json`)
