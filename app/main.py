from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import asyncio
import pyaudio
import wave
import time
import os
import tempfile
import openai
from typing import List

# Placeholder for your OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY')

app = FastAPI()

class ConnectionManager:
    """Manages active WebSocket connections."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(connection)

manager = ConnectionManager()

# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK_SECONDS = 5  # duration of each audio chunk in seconds

async def transcribe_audio(audio_bytes: bytes) -> str:
    """Send audio bytes to OpenAI Whisper API and return transcription."""
    # Write bytes to temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        with wave.open(tmp.name, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(pyaudio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(audio_bytes)
        tmp.seek(0)
        audio_file = open(tmp.name, 'rb')
        try:
            result = openai.Audio.transcribe("whisper-1", audio_file)
            text = result.get('text', '')
        finally:
            audio_file.close()
        os.unlink(tmp.name)
    return text

async def audio_loop():
    """Continuously capture microphone audio, transcribe, and broadcast."""
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    start_time = time.time()

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        if time.time() - start_time >= CHUNK_SECONDS:
            audio_data = b''.join(frames)
            frames = []
            start_time = time.time()
            text = await transcribe_audio(audio_data)
            if text:
                await manager.broadcast(text)

@app.on_event("startup")
async def startup_event():
    # Start audio capturing loop as background task
    asyncio.create_task(audio_loop())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection open
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def get_index():
    with open(os.path.join('static', 'index.html')) as f:
        return HTMLResponse(f.read())
