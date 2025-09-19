# Voice Agent Hackathon - Ultra Setup

Ready-to-use voice agent with [AssemblyAI](https://assemblyai.com) + [Rime](https://rime.ai) + [LiveKit](https://livekit.io). Just copy-paste these commands.

## 🚀 One-Command Setup

```bash
# Clone and setup
git clone https://github.com/darinkishore/voice-agent-hackathon.git
cd voice-agent-hackathon
```

```bash
# Install dependencies
uv sync
```

```bash
# Setup LiveKit credentials (requires LiveKit CLI - install from https://docs.livekit.io/home/cli/cli-setup)
lk cloud auth
lk app env -w -d .env.local
```

```bash
# Download models
uv run python src/agent.py download-files
```

```bash
# Start the agent
uv run python src/agent.py dev
```

## 🎯 Test Your Agent

Open: https://agents-playground.livekit.io/#cam=0&mic=1&screen=0&video=0&audio=1&chat=1&theme_color=cyan

WebSocket URL: Check your `.env.local` file for `LIVEKIT_URL`

## 🔧 Troubleshooting

**Noisy environment?** Use headphones with noise cancellation or test with text input instead of microphone.

## 🧪 Run Tests

```bash
uv run pytest
```

## 🚀 Deploy to Production

This includes a working `Dockerfile`. See [deployment guide](https://docs.livekit.io/agents/ops/deployment/).

## 📱 Frontend Options

- **React**: [`agent-starter-react`](https://github.com/livekit-examples/agent-starter-react)
- **iOS/macOS**: [`agent-starter-swift`](https://github.com/livekit-examples/agent-starter-swift)
- **Flutter**: [`agent-starter-flutter`](https://github.com/livekit-examples/agent-starter-flutter)
- **React Native**: [`agent-starter-react-native`](https://github.com/livekit-examples/agent-starter-react-native)
- **Android**: [`agent-starter-android`](https://github.com/livekit-examples/agent-starter-android)
- **Web Embed**: [`agent-starter-embed`](https://github.com/livekit-examples/agent-starter-embed)
- **Telephony**: [📚 Documentation](https://docs.livekit.io/agents/start/telephony/)

## 🤖 Models

Uses **AssemblyAI** (speech-to-text) + **Rime** (text-to-speech) + **GPT-4o-mini** (LLM). No extra accounts needed.

**Customize voices** in `src/agent.py`:
```python
session = AgentSession(
    tts="rime/arcana:andromeda"  # Change voice here
)
```

See [Rime voices](https://docs.rime.ai/api-reference/voices) for options.

**Use your own accounts:**
```bash
# AssemblyAI plugin
uv add livekit-agents[assemblyai]

# Rime plugin
uv add livekit-agents[rime]
```

**Different LLM:**
```python
session = AgentSession(
    llm="azure/gpt-4o-mini"  # Or other models
)
```
