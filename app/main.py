
import os
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.services.speech_service import SpeechService
from app.services.receipt_service import ReceiptService
from app.services.question_service import QuestionService
from app.services.voice_service import VoiceService


# ==========================================
# CREATE FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="Voice Receipt Assistant",
    description="AI assistant for asking questions about receipts using voice.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "FRONTEND_ORIGINS",
            "http://127.0.0.1:3000,http://localhost:3000"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# CREATE SERVICES
# ==========================================

speech_service = SpeechService()
receipt_service = ReceiptService()
question_service = QuestionService()
voice_service = VoiceService()


# ==========================================
# TEMPORARY STORAGE
# ==========================================

UPLOAD_DIRECTORY = str(Path(__file__).resolve().parent.parent / "uploads")

os.makedirs(
    UPLOAD_DIRECTORY,
    exist_ok=True
)


# Store the most recently extracted receipt
current_receipt = None


# ==========================================
# HOME
# ==========================================

@app.get("/")
def root():

    return {
        "message": "Voice Receipt Assistant is running!"
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "models": {
            "receipt": receipt_service.model_name,
            "receipt_loaded": receipt_service.model is not None,
            "speech": os.getenv("SPEECH_MODEL", "openai/whisper-tiny"),
            "speech_loaded": speech_service.pipe is not None,
        }
    }


# ==========================================
# TRANSCRIBE VOICE
# ==========================================

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(status_code=400, detail="Please choose an audio file.")

    file_extension = os.path.splitext(
        file.filename
    )[1]

    filename = (
        f"{uuid.uuid4()}"
        f"{file_extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIRECTORY,
        filename
    )

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    try:

        text = speech_service.transcribe(
            file_path
        )

        return {
            "success": True,
            "text": text
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {error}"
        )


# ==========================================
# RECEIPT OCR
# ==========================================

@app.post("/receipt")
async def extract_receipt(
    file: UploadFile = File(...)
):

    global current_receipt

    if not file.filename:
        raise HTTPException(status_code=400, detail="Please choose a receipt image.")

    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".pdf"}
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail="Receipt OCR supports JPG, PNG, WEBP, BMP images, and PDF documents."
        )

    filename = (
        f"{uuid.uuid4()}"
        f"{file_extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIRECTORY,
        filename
    )

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    try:

        receipt = receipt_service.extract_document(
            file_path
        )

        current_receipt = receipt

        receipt_data = (
            receipt.model_dump()
            if hasattr(receipt, "model_dump")
            else receipt.dict()
        )

        return {
            "success": True,
            "receipt": receipt_data
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Receipt processing failed: {error}"
        )


# ==========================================
# ASK QUESTION
# ==========================================

@app.post("/ask")
async def ask_question(
    question: str
):

    if current_receipt is None:

        raise HTTPException(
            status_code=400,
            detail="Please upload a receipt first."
        )

    answer = question_service.answer(
        question,
        current_receipt
    )

    return {
        "success": True,
        "question": question,
        "answer": answer
    }


# ==========================================
# FULL VOICE ASSISTANT
# ==========================================

@app.post("/voice-assistant")
async def voice_assistant(
    file: UploadFile = File(...)
):

    if current_receipt is None:

        raise HTTPException(
            status_code=400,
            detail="Please upload a receipt first."
        )

    file_extension = os.path.splitext(
        file.filename
    )[1]

    filename = (
        f"{uuid.uuid4()}"
        f"{file_extension}"
    )

    audio_path = os.path.join(
        UPLOAD_DIRECTORY,
        filename
    )

    with open(audio_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    try:

        # STEP 1
        # Voice → Text

        question = speech_service.transcribe(
            audio_path
        )

        # STEP 2
        # Text → Answer

        answer = question_service.answer(
            question,
            current_receipt
        )

        # STEP 3
        # Answer → Voice

        answer_audio = voice_service.text_to_speech(
            answer
        )

        return {
            "success": True,
            "question": question,
            "answer": answer,
            "audio_file": answer_audio
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ==========================================
# PLAY GENERATED AUDIO
# ==========================================

@app.get("/audio/{filename}")
def get_audio(filename: str):

    file_path = os.path.join(
        UPLOAD_DIRECTORY,
        filename
    )

    if not os.path.exists(file_path):

        raise HTTPException(
            status_code=404,
            detail="Audio file not found."
        )

    return FileResponse(
        file_path,
        media_type="audio/mpeg"
    )
