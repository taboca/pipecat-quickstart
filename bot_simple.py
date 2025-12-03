#
# Minimal Daily room joiner using OpenAI for STT/LLM/TTS.
#
# Reads ROOM_URL and DAILY_TOKEN from the environment; if DAILY_TOKEN is
# missing but DAILY_API_KEY is set, it will mint a meeting token for that room.
#

import asyncio
import os
import time
import requests

from dotenv import load_dotenv
from loguru import logger

from pipecat.frames.frames import LLMMessagesUpdateFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.tts import OpenAITTSService
from pipecat.transports.daily.transport import DailyParams, DailyTransport, DailyTransportMessageFrame


load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DAILY_API_KEY = os.getenv("DAILY_API_KEY")
DAILY_TOKEN = os.getenv("DAILY_TOKEN")
ROOM_URL = os.getenv("ROOM_URL")


def ensure_daily_token() -> str:
    """Return DAILY_TOKEN if set; otherwise mint one for ROOM_URL using DAILY_API_KEY."""
    if DAILY_TOKEN:
        return DAILY_TOKEN
    if not DAILY_API_KEY:
        raise RuntimeError("Set DAILY_TOKEN or DAILY_API_KEY in the environment.")
    if not ROOM_URL:
        raise RuntimeError("Set ROOM_URL in the environment.")
    room_name = ROOM_URL.rstrip("/").split("/")[-1]
    r = requests.post(
        "https://api.daily.co/v1/meeting-tokens",
        headers={"Authorization": f"Bearer {DAILY_API_KEY}", "Content-Type": "application/json"},
        json={"properties": {"room_name": room_name, "is_owner": True}},
        timeout=15,
    )
    r.raise_for_status()
    tok = r.json()["token"]
    logger.info("Minted Daily token for %s", room_name)
    return tok


async def send_room_meta(transport: DailyTransport, text: str):
    payload = {"type": "meta", "text": text, "ts": int(time.time() * 1000)}
    frame = DailyTransportMessageFrame(message=payload)
    await transport.output().send_message(frame)


async def main():
    if not OPENAI_API_KEY:
        raise RuntimeError("Set OPENAI_API_KEY in the environment.")
    if not ROOM_URL:
        raise RuntimeError("Set ROOM_URL in the environment.")

    token = ensure_daily_token()

    tts = OpenAITTSService(
        api_key=OPENAI_API_KEY,
        model="gpt-4o-mini-tts",
        voice="verse",
    )
    llm = OpenAILLMService(api_key=OPENAI_API_KEY, model="gpt-4o")

    messages = [
        {
            "role": "system",
            "content": (
                "You are a concise, friendly assistant in a Daily call. "
                "Your responses are spoken back to participants."
            ),
        },
    ]

    context = LLMContext(messages)
    context_aggregator = LLMContextAggregatorPair(context)

    transport = DailyTransport(
        ROOM_URL,
        token,
        "Pipecat Bot",
        DailyParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            transcription_enabled=True,
        ),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=True,
            report_only_initial_ttfb=True,
        ),
    )

    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        logger.info("First participant joined: {}", participant.get("id"))
        await transport.capture_participant_transcription(participant["id"])
        messages.append(
            {
                "role": "system",
                "content": "Say hello and introduce yourself briefly.",
            }
        )
        await task.queue_frames([LLMMessagesUpdateFrame(messages=messages, run_llm=True)])
        await send_room_meta(transport, "Bot is ready. Transcription is ON.")

    @transport.event_handler("on_participant_left")
    async def on_participant_left(transport, participant, reason):
        logger.info("Participant left: {} | reason={}", participant, reason)
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False, force_gc=True)

    logger.warning("Join the bot in this room: %s", ROOM_URL)
    await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())
