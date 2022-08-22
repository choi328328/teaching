# %%
from pytube import YouTube
import moviepy.editor as mp
import moviepy.video.fx.all as vfx
from pydub import AudioSegment
import librosa
import soundfile as sf
from pyrubberband.pyrb import time_stretch
from pytube import Playlist
import shutil
import os
from loguru import logger

def save_youtube(url, outpath=None, rate=1.0):
    yt = YouTube(url)
    stream_audio = yt.streams.filter(only_audio=True).first()
    stream_audio.download(filename=f'{outpath}.m4a')

    os.remove(f'{outpath}.m4a')
 
    # speed x1.5
    # y, sr = librosa.load(outpath, sr=None)
    # if rate != 1.0:
    #     y_fast=time_stretch(y, sr, rate)
    #     sf.write(outpath, y_fast, 44100)
    #  # save as mp3 for storage
    
    wav_audio = AudioSegment.from_file(f'{outpath}.m4a', format="m4a")
    wav_audio.export(f'/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/잡동사니/음악/{outpath}.mp3', format="mp3")
  
url = 'https://www.youtube.com/watch?v=kOCkne-Bku4'
outpath = 'ParisinRain'
logger.info(outpath)
save_youtube(url, outpath)
# %%
