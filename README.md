# FastAPI Whisper Transcription Example

This project demonstrates a minimal FastAPI backend that captures microphone audio, transcribes it with OpenAI Whisper, and streams the transcription to a browser via WebSockets.

## Requirements

- Python 3.9+
- `fastapi`, `uvicorn`, `pyaudio`, `openai`

Install dependencies:

```bash
pip install fastapi uvicorn pyaudio openai
```

Set your OpenAI API key in the environment:

```bash
export OPENAI_API_KEY=your_key_here
```

## Running the backend

Start the FastAPI app with uvicorn:

```bash
uvicorn app.main:app --reload
```

## Running the frontend

Serve the `static/` directory using any simple HTTP server. For example:

```bash
python -m http.server --directory static 8000
```

Then open `http://localhost:8000` in your browser. The page will connect to the WebSocket endpoint and display live transcription results.

