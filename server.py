import os, re, uuid, subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from faster_whisper import WhisperModel
import yt_dlp

BASE=Path(__file__).parent
WORK=BASE/"jobs"; WORK.mkdir(exist_ok=True)
app=FastAPI(title="Clipper AI")
model=None

class Request(BaseModel):
    url: HttpUrl
    prompt: str=""
    count: int=5
    duration: int=60
    format: str="9:16"
    language: str="auto"

def run(args):
    p=subprocess.run(args,capture_output=True,text=True)
    if p.returncode: raise RuntimeError((p.stderr or p.stdout)[-1800:])
    return p.stdout

@app.get("/api/health")
def health(): return {"ok":True}

@app.post("/api/process")
def process(req:Request):
    global model
    if not 1 <= req.count <= 100: raise HTTPException(400,"Choose between 1 and 100 clips.")
    if req.duration not in [30,45,60,90,180]: raise HTTPException(400,"Unsupported clip length.")
    if req.format not in ["9:16","1:1","16:9"]: raise HTTPException(400,"Unsupported format.")
    job=uuid.uuid4().hex; folder=WORK/job; folder.mkdir()
    try:
        opts={"outtmpl":str(folder/"source.%(ext)s"),"format":"bestvideo[height<=1080]+bestaudio/best[height<=1080]","merge_output_format":"mp4","noplaylist":True,"quiet":True}
        with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([str(req.url)])
        files=list(folder.glob("source.*"))
        if not files: raise RuntimeError("No downloadable video was found. The site may block access or require login.")
        src=files[0]
        if model is None: model=WhisperModel(os.getenv("WHISPER_MODEL","base"),device="cpu",compute_type="int8")
        segments,info=model.transcribe(str(src),language=None if req.language=="auto" else req.language, vad_filter=True)
        transcript=[{"start":float(s.start),"end":float(s.end),"text":s.text.strip()} for s in segments if s.text.strip()]
        if not transcript: raise RuntimeError("No speech was detected in this video.")
        # Score transcript windows for useful, emphatic language, then select spaced candidates.
        words=re.compile(r"\b(important|secret|tip|mistake|why|how|best|never|always|learn|remember|because|first|finally|problem|solution|amazing|incredible|actually|اس|کیوں|कैसे|क्यों)\b",re.I)
        candidates=[]
        for i,s in enumerate(transcript):
            start=s["start"]; end=min(start+req.duration,s["end"]+req.duration*.75)
            chunk=" ".join(x["text"] for x in transcript if x["start"]<end and x["end"]>start)
            if end-start>=8:
                score=len(words.findall(chunk))+min(len(chunk)/350,2)
                candidates.append((score,start,end,chunk[:90]))
        candidates.sort(reverse=True)
        chosen=[]
        for score,start,end,title in candidates:
            if all(abs(start-x[1])>req.duration*.65 for x in chosen):
                chosen.append((score,start,end,title))
            if len(chosen)>=req.count: break
        chosen.sort(key=lambda x:x[1])
        if not chosen: raise RuntimeError("Could not find suitable speech sections.")
        clips=[]
        for n,(_,start,end,title) in enumerate(chosen,1):
            out=folder/f"clip-{n:02}.mp4"
            vf={"9:16":"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920","1:1":"scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080","16:9":"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"}[req.format]
            run(["ffmpeg","-y","-ss",str(start),"-i",str(src),"-t",str(end-start),"-vf",vf,"-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-movflags","+faststart",str(out)])
            clips.append({"url":f"/jobs/{job}/{out.name}","title":title or f"Clip {n}"})
        return {"message":f"Created {len(clips)} clips. AI transcription was used to identify speech sections; review clips before publishing.","clips":clips}
    except Exception as e:
        raise HTTPException(500,str(e))
    finally:
        # Keep output folder available for downloads; source and intermediate files can be large.
        for f in folder.glob("source.*"):
            try: f.unlink()
            except OSError: pass

app.mount("/jobs",StaticFiles(directory=WORK),name="jobs")
app.mount("/",StaticFiles(directory=BASE/"static",html=True),name="static")
