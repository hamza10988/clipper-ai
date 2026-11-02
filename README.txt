CLIPPER AI — FREE / OPEN-SOURCE STARTER

WHAT THIS PROJECT DOES
- Accepts a public video URL through a backend using yt-dlp.
- Transcribes speech locally with faster-whisper.
- Picks candidate speech sections using transcript scoring.
- Cuts and exports MP4 clips with FFmpeg in the chosen aspect ratio.
- The app allows up to 100 requested clips per job; this is not a promise of unlimited server capacity.

IMPORTANT LIMITATIONS
- This is a self-hosted starter, not a hosted public website.
- YouTube/TikTok/Instagram/Facebook links may fail due to login, region, age, DRM, anti-bot, or platform restrictions. Use only content you own or have permission to process.
- Transcript scoring is a basic AI-assisted heuristic, not a human-level viral-moment guarantee.
- Captions are transcribed but are not yet burned into the video. Add caption rendering as a later feature.
- Free hosting usually sleeps, limits CPU/RAM, storage, runtime, and bandwidth. No honest service can guarantee unlimited free AI processing.

RUN LOCALLY
1. Install Python 3.10+, FFmpeg, and ffprobe.
2. Open a terminal in this folder.
3. Run: python -m venv .venv
4. Activate it:
   Windows: .venv\Scripts\activate
   macOS/Linux: source .venv/bin/activate
5. Run: pip install -r requirements.txt
6. Run: uvicorn server:app --host 0.0.0.0 --port 8000
7. Open http://localhost:8000

DEPLOYMENT
The frontend and backend must be deployed together on a Python host with FFmpeg installed and enough RAM/CPU/disk. A static-only host such as basic Netlify Drop cannot run this processing backend. Check current free-tier limits before choosing a host.
