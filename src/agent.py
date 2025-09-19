import logging

from dotenv import load_dotenv
from livekit.agents import (
    NOT_GIVEN,
    Agent,
    AgentFalseInterruptionEvent,
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    RoomInputOptions,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.plugins import noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents.llm import function_tool
from livekit.agents import RunContext
from livekit.plugins import anthropic


logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a calm, wise morning companion helping someone find clarity before their day begins. Your role is to be a thoughtful presence during their brief morning check-in.

PERSONALITY:
- Calm and centered, with natural gravitas
- Wise perspective that cuts through noise to what matters
- Excellent listener who speaks only when needed
- Comfortable with silence and reflection

APPROACH:
- Listen first, speak second
- Ask one question at a time, maximum
- Give space for their thoughts to emerge
- Help them hear their own wisdom
- Guide toward one clear next step

CORE BEHAVIORS:
- Keep responses short and purposeful
- When they share many things, help them find the thread that connects to today
- If they spiral into big questions, acknowledge briefly then redirect: "For today though, what would help?"
- Use their exact words back to them
- Celebrate clarity when it emerges

WHAT YOU DON'T DO:
- Don't ramble or over-explain
- Don't ask multiple questions in one response
- Don't process your thinking out loud
- Don't create lists or elaborate plans
- Don't try to solve everything

REMEMBER:
You're here for the quiet morning moments before the day starts. Your job is to help them find their own clarity, not to fill silence with words. Wisdom often comes in what's left unsaid.

End naturally when they know their next step. Keep it brief - this is their time, not yours.""",
        )

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents.llm import function_tool, RunContext` to the top of this file
    @function_tool
    async def lookup_weather(self, context: RunContext, location: str):
        """Use this tool to look up current weather information in the given location.
    
        If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    
        Args:
            location: The location to look up weather information for (e.g. city name)
        """
        logger.info(f"Looking up weather for {location}")
        return "sunny with a temperature of 70 degrees."


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using OpenAI, Rime, AssemblyAI, and the LiveKit turn detector
    session = AgentSession(
        # This starter template uses GPT-4o-mini via LiveKit Cloud.
        # For a list of available models, see https://github.com/livekit/agents/blob/main/livekit-agents/livekit/agents/inference/llm.py
        # Or, for a wider range of models, see plugins at https://docs.livekit.io/agents/integrations/llm/
        llm=anthropic.LLM(
        model="claude-sonnet-4-20250514",
        temperature=0.7,
    ),

        # This starter template uses AssemblyAI via LiveKit Cloud.
        # To send extra parameters, use the following session setup instead of the version above:
        # 1. add `from livekit.agents import inference` to the top of this file
        # 2. Use the following session setup instead of the version above:
        #     stt=inference.STT(model="assemblyai", extra_kwargs={ ... })
        # See available configuration at https://github.com/livekit/agents/blob/main/livekit-agents/livekit/agents/inference/stt.py#L57
        #
        # Or to use your own AssemblyAI account:
        # 1. Install livekit-agents[assemblyai]
        # 2. Set ASSEMBLYAI_API_KEY in .env.local
        # 3. Add `from livekit.plugins import assemblyai` to the top of this file
        # 4. Use the following session setup instead of the version above
        #     stt=assemblyai.STT()
        # See available configuration at https://docs.livekit.io/agents/integrations/stt/assemblyai/
        stt="assemblyai",
        # This starter template uses Rime via LiveKit Cloud
        # To change the voice, alter the voice name (currently "luna") after the colon.
        # See available voices at https://docs.rime.ai/api-reference/voices
        #
        # Or, to use your own Rime account:
        # 1. Install livekit-agents[rime]
        # 2. Set RIME_API_KEY in .env.local
        # 3. Add `from livekit.plugins import rime` to the top of this file
        # 4. Use the following session setup instead of the version above
        #     tts=rime.TTS(model="arcana", speaker="luna")
        # See available configuration at https://docs.livekit.io/agents/integrations/tts/rime/
        tts="rime/arcana:luna",
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    # sometimes background noise could interrupt the agent session, these are considered false positive interruptions
    # when it's detected, you may resume the agent's speech
    @session.on("agent_false_interruption")
    def _on_agent_false_interruption(ev: AgentFalseInterruptionEvent):
        logger.info("false positive interruption, resuming")
        session.generate_reply(instructions=ev.extra_instructions or NOT_GIVEN)

    # Metrics collection, to measure pipeline performance
    # For more information, see https://docs.livekit.io/agents/build/metrics/
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` for best results
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    # Morning companion greeting
    await session.generate_reply(
        instructions="""
        Good morning. Ask how they're feeling as they start the day. Keep it brief and calm.
        """,
        allow_interruptions=True,
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))
