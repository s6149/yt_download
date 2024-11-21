from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from yt_dlp import YoutubeDL
from pydantic import BaseModel
import asyncio
from typing import Optional
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    format: Optional[str] = "mp4"
    quality: Optional[str] = "best"

@app.post("/download")
async def download_video(request: DownloadRequest):
    try:
        output_dir = "downloads"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' if request.format == "mp4" else 'bestaudio[ext=m4a]/bestaudio',
            'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }] if request.format == "mp4" else [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': '/usr/bin/ffmpeg',  # 指定 ffmpeg 路徑
            'verbose': True,  # 顯示詳細日誌
        }
        
        def download():
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(request.url, download=True)
                return ydl.prepare_filename(info), info
                
        filename, info = await asyncio.to_thread(download)
        
        # 修正音訊檔案的副檔名
        if request.format == "mp3":
            filename = os.path.splitext(filename)[0] + '.mp3'
        
        return FileResponse(
            path=filename,
            filename=os.path.basename(filename),
            media_type="video/mp4" if request.format == "mp4" else "audio/mp3"
        )

    except Exception as e:
        print(f"Download error: {str(e)}")  # 增加錯誤輸出
        raise HTTPException(status_code=400, detail=f"Download failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3206)