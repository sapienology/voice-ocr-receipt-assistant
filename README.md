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

## Docker deployment

Build and run the complete app as one container:

```powershell
docker build -t voice-ocr-receipt-assistant .
docker run --rm -p 8000:8000 -v receipt-uploads:/app/uploads voice-ocr-receipt-assistant
```

Open `http://localhost:8000`. The container serves both the frontend and API.
OCR and speech model files download on first use and are cached inside the
container unless a model cache volume is configured.

The receipt OCR uses PaddleOCR's lightweight `PP-OCRv5_mobile` detector and
recognizer, a free pretrained model that handles varied receipt layouts while
using less memory on small deployments. Speech transcription uses the lighter
`openai/whisper-tiny`. Hugging Face downloads each model on its first use; set
`RECEIPT_MODEL` or `SPEECH_MODEL` to a local model path when deploying without
internet access.

Render's 512 MB service tier may still be too small for PaddlePaddle OCR during
the first receipt request. Use a larger memory instance for OCR, or keep OCR
disabled on the smallest tier and use the fallback response.