# Project Arena

Project Arena is a fan-made Telegram community bot inspired by high-energy gaming culture. It preserves the original `$DRD` theme while focusing promotion on the Telegram community rather than direct token marketing.

## Version 1 features

- Stable Telegram polling with one generic message handler
- `/start`, `/arena`, `/drd`, `/news`, `/about`
- Public Doc-related headlines through a cached RSS source
- Optional Telegram channel CTA shown sparingly
- Lightweight Flask health endpoint for hosting platforms
- No database duplication and no second bot instance
- No credentials committed to GitHub

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `TELEGRAM_BOT_TOKEN` and optionally `TELEGRAM_CHANNEL_URL`, then run:

```bash
python main.py
```

## Current limits

Version 1 does not yet analyze YouTube transcripts, ingest Reddit, publish on X, use an LLM, or maintain long-term Arena Memory. Those should be added as separate modules after the Telegram foundation is tested.

## Planned modules

- Arena Brain: contextual AI chat
- Arena Memory: sourced event timeline
- Arena Media: YouTube transcript and timestamp extraction
- Arena News: multi-source ingestion and deduplication
- Arena X: draft generation with Telegram approval and strict anti-spam limits

## Disclaimer

Project Arena is fan-made and is not affiliated with Dr Disrespect, YouTube, X, Telegram, or any token issuer. Crypto references are community-themed and are not financial advice.
