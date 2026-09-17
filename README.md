# Voice Invoice Receipt Assistant

An AI-powered voice assistant for interacting with invoice and receipt information.

## Project idea

The user can upload a receipt and ask questions about it using their voice.

Example:

"What was the total?"

The system:

1. Converts speech to text using Whisper.
2. Processes the receipt using OCR/Donut.
3. Understands the question.
4. Finds the requested information.
5. Converts the answer to speech.
6. Returns the audio response.

## Architecture

User Voice
    ↓
Whisper
    ↓
Text Question
    ↓
Receipt OCR / Donut
    ↓
Receipt Data
    ↓
Question Service
    ↓
Answer
    ↓
Text-to-Speech
    ↓
Audio Response

## Technologies

- Python
- FastAPI
- Hugging Face Transformers
- Whisper
- Donut
- PyTorch
- gTTS
- Pydantic

## Running the project

Activate the virtual environment:

```bash
source venv/Scripts/activate
```

Install dependencies and start both servers from the project directory:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
python serve_frontend.py
```

Open `http://localhost:3000`. The frontend calls the API on port 8001. For a
different frontend URL, set `FRONTEND_ORIGINS` to a comma-separated list of
allowed origins before starting Uvicorn.

The receipt OCR uses PaddleOCR `PP-OCRv6_medium`, a free pretrained detector
and recognizer that handles varied receipt layouts. Speech transcription uses the lighter
`openai/whisper-tiny`. Hugging Face downloads each model on its first use; set
`RECEIPT_MODEL` or `SPEECH_MODEL` to a local model path when deploying without
internet access.