# Audio Transcription App

## Overview
This application is a FastAPI-based web app that allows users to record audio, transcribe it, summarize the text, and store it in a structured format. Users can browse and retrieve saved transcriptions based on dates.

## Features
- **Record Audio:** Users can record their voice directly in the app.
- **Transcribe & Summarize:** Converts speech to text and generates a summary using AI.
- **Save Transcriptions:** Appends transcriptions to a structured text file (`transcriptions.txt`).
- **Browse Transcriptions by Date:** Users can select a date to view all transcriptions recorded on that day.
- **View Summaries in Alert:** Clicking a date triggers an alert displaying concatenated summaries.
- **UI Enhancements:**
  - **Title uses `SFSportsNight.ttf`** (stored in `/static/fonts`)
  - **All other text uses Tahoma**
  - **Date selection buttons are styled with `.date-button` CSS**

## API Endpoints
### 1️⃣ **Append a New Transcription**
**`POST /append/`**
- Saves a transcript and summary with a timestamp.
- Data format:
```json
{
  "transcript": "Original spoken text",
  "summary": "Summarized text"
}
```

### 2️⃣ **List Available Transcription Dates**
**`GET /transcripts/dates`**
- Returns all dates where transcriptions exist.
- Dates are sorted in **descending order** (newest first).

### 3️⃣ **Retrieve Transcriptions for a Specific Date**
**`GET /transcripts/{date}`**
- Fetches summaries stored for the given date.
- Returns a JSON response:
```json
{
  "summaries": [
    "Summary 1",
    "Summary 2"
  ]
}
```

## How It Works
1. **Start the FastAPI server:**
   ```sh
   python main.py
   ```
2. **Open the web app in a browser:**
   ```
   http://127.0.0.1:8000
   ```
3. **Record & Save Transcriptions**
   - Click the **Record** button to start recording.
   - Stop recording, then the text will be transcribed and summarized.
   - Click **Save** to store the transcription.
4. **Retrieve Transcriptions by Date**
   - Click **Show Available Dates**.
   - Select a date → an **alert box** will display concatenated summaries.

## File Structure
```
/static
  ├── css/  # Stylesheets
  ├── fonts/  # Custom fonts (SFSportsNight.ttf)
  ├── js/  # JavaScript logic
/transcripts
  ├── transcriptions.txt  # Stores all transcriptions
index.html  # Frontend UI
main.py  # FastAPI backend
```

## Notes
- Ensure `SFSportsNight.ttf` is placed in `/static/fonts/`.
- The app uses **Tahoma** for all text except the title.
- Clicking on a date **only shows an alert with transcriptions** (no separate page).

🚀 **Enjoy using the Audio Transcription App!** 🚀

