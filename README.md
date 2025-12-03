# Demo of a Voice Assistant Bot entering a Daily.co Meeting

This focuses on the simple path: join a specific Daily room with OpenAI STT/LLM/TTS via `bot_simple.py`. For the full upstream quickstart (RTVI/local WebRTC server, multiple transports), see: https://github.com/pipecat-ai/pipecat-quickstart

## Local run (Daily static room)

### Prerequisites

#### Environment

- Python 3.10 or later
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager installed

#### API key and room
- `OPENAI_API_KEY` (required) for STT/LLM/TTS.
- `ROOM_URL` for the Daily room you want to join.
- Either `DAILY_TOKEN` for that room, or `DAILY_API_KEY` that can mint a token for that same Daily domain.

Daily room + API key sources:
- Your own Daily dashboard (e.g., `https://your-domain.daily.co/...` + its API key).
- Pipecat Cloud “Daily” panel (shows a Pipecat-managed domain like `https://cloud-....daily.co/...` + its API key).
- Domain/key must match: you can only mint tokens for rooms on the same Daily domain as the API key you use.

### Setup

Navigate to the quickstart directory and set up your environment.

1. Clone this repository

   ```bash
   git clone https://github.com/pipecat-ai/pipecat-quickstart.git
   cd pipecat-quickstart
   ```

2. Configure your keys:

   Create a `.env` file:

   ```bash
   cp env.example .env
   ```

   Then, add your keys:

   ```ini
   OPENAI_API_KEY=your_openai_api_key
   DAILY_API_KEY=your_daily_api_key          # optional if minting tokens
   ROOM_URL=https://your-domain.daily.co/room # optional; for static room joins
   DAILY_TOKEN=your_meeting_token             # optional; or mint via DAILY_API_KEY
   ```

3. Set up a virtual environment and install dependencies

   ```bash
   uv sync
   ```

### Run your bot locally (static room)

```bash
uv run bot_simple.py
```

Env needed: `OPENAI_API_KEY`, `ROOM_URL`, plus either `DAILY_TOKEN` or `DAILY_API_KEY` (domain must match the room).

To use this path:
1) Copy `env.example` → `.env` and fill:
   - `OPENAI_API_KEY`
   - `ROOM_URL=https://<your-daily-domain>.daily.co/<room>`
   - `DAILY_TOKEN=<meeting-token>` (or omit and set `DAILY_API_KEY` to mint one)
2) Run: `uv sync && uv run bot_simple.py`
This does not start the localhost WebRTC server; it joins your specified Daily room directly.

If you need the full upstream quickstart flow (RTVI runner, local WebRTC server at http://localhost:7860, multiple transports), see: https://github.com/pipecat-ai/pipecat-quickstart

---

## More

For the full upstream quickstart (RTVI runner, localhost dev server, and broader Pipecat Cloud deployment docs), see: https://github.com/pipecat-ai/pipecat-quickstart
