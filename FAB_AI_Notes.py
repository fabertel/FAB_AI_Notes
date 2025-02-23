

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel
import os
import re
import datetime
import shutil
from dotenv import load_dotenv

class TranscriptionData(BaseModel):
    transcript: str
    summary: str

# Load environment variables from .env
load_dotenv()

app = FastAPI()
# Get OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API Key! Add it to the .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)

TRANSCRIPTS_DIR = os.path.abspath("transcripts")
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
TRANSCRIPT_FILE = os.path.join(TRANSCRIPTS_DIR, "transcriptions.txt")

# Cost estimation constants
WHISPER_COST_PER_MINUTE = 0.006  # Approx cost per minute for Whisper API
GPT4_COST_PER_1K_TOKENS = 0.03   # Approx cost per 1K tokens for GPT-4

# Mount static directory for frontend files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/record/")
async def record_audio(file: UploadFile = File(...)):
    try:
        temp_audio_path = f"temp_{file.filename}"
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ensure file is closed before processing
        file.file.close()
        
        with open(temp_audio_path, "rb") as audio_file:
            transcript_response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            transcript = transcript_response.text
        
        # Estimate cost for Whisper transcription
        audio_duration_minutes = os.path.getsize(temp_audio_path) / (16000 * 60 * 2)  # Approximation for 16kHz WAV
        whisper_cost = audio_duration_minutes * WHISPER_COST_PER_MINUTE
        
        # Translate transcript to Italian
        translation_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Translate the following text to Italian, ensuring accurate transcription."},
                {"role": "user", "content": transcript}
            ]
        )
        transcript_italian = translation_response.choices[0].message.content
        translation_tokens = translation_response.usage.total_tokens
        translation_cost = (translation_tokens / 1000) * GPT4_COST_PER_1K_TOKENS
        
        # Generate summary in Italian
        summary_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Summarize the following transcript in Italian."},
                {"role": "user", "content": transcript_italian}
            ]
        )
        summary_italian = summary_response.choices[0].message.content
        summary_tokens = summary_response.usage.total_tokens
        summary_cost = (summary_tokens / 1000) * GPT4_COST_PER_1K_TOKENS
        
        total_cost = whisper_cost + translation_cost + summary_cost
        
        os.remove(temp_audio_path)
        
        return {
            "message": "Processing complete",
            "transcript": transcript_italian,
            "summary": summary_italian,
            "tokens_used": {
                "translation": translation_tokens,
                "summary": summary_tokens
            },
            "cost_estimate": {
                "whisper": whisper_cost,
                "translation": translation_cost,
                "summary": summary_cost,
                "total": total_cost
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/append/")
async def append_transcription(data: TranscriptionData):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        separator = "\n" + "=" * 50 + "\n"
        
        with open(TRANSCRIPT_FILE, "a", encoding="utf-8") as f:
            f.write(f"{separator}Timestamp: {timestamp}\n")
            f.write(f"ORIG : {data.transcript}\n")
            f.write(f"SUMM : {data.summary}\n")
        
        return {"message": "Transcription appended", "filename": TRANSCRIPT_FILE}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/transcripts/")
async def list_transcriptions():
    try:
        if not os.path.exists(TRANSCRIPT_FILE):
            return {"transcriptions": []}  # Return empty list if no transcription file exists

        dates = set()
        with open(TRANSCRIPT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                match = re.search(r"Timestamp: (\d{4}-\d{2}-\d{2})", line)
                if match:
                    dates.add(match.group(1))

        return {"transcriptions": sorted(dates)}
    except Exception as e:
        print("Error listing transcriptions:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/transcripts/dates")
async def list_transcription_dates():
    try:
        if not os.path.exists(TRANSCRIPT_FILE):
            return JSONResponse(content={"dates": []})

        dates = set()
        with open(TRANSCRIPT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                match = re.search(r"Timestamp: (\d{4}-\d{2}-\d{2})", line)
                if match:
                    dates.add(match.group(1))

        return JSONResponse(content={"dates": sorted(dates, reverse=True)})

    except Exception as e:
        print("Error in /transcripts/dates:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/transcripts/{date}")
async def get_transcriptions_by_date(date: str):
    try:
        if not os.path.exists(TRANSCRIPT_FILE):
            return JSONResponse(content={"summaries": "No transcriptions available."})

        summaries = []
        capture = False
        with open(TRANSCRIPT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if re.search(fr"Timestamp: {date}", line):
                    print("MATCHED TIMESTAMP:", date)  # Debugging log
                    capture = True
                elif capture and line.startswith("SUMM :"):
                    summary_text = line.replace("SUMM :", "").strip()
                    print("CAPTURED SUMMARY:", summary_text)  # Debugging log
                    summaries.append(summary_text)
                elif capture and re.search(r"=+", line):  # End of entry
                    capture = False

        return JSONResponse(content={"summaries": summaries if summaries else ["No summaries found for this date."]})
        
    
    except Exception as e:
        print("Error in /transcripts/{date}:", str(e))
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

