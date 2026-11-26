"""Center user-provided stereo clips without changing duration or pitch."""
from pathlib import Path
import wave, struct

ROOT=Path(__file__).resolve().parents[1]
for name in ('footstep.wav',):
    path=ROOT/'Assets/audio'/name
    with wave.open(str(path),'rb') as src:
        channels,width,rate,frames,_,_=src.getparams()
        raw=src.readframes(frames)
    if channels != 2 or width != 2:
        continue
    values=struct.unpack('<'+'h'*(frames*channels),raw)
    centered=[]
    for i in range(0,len(values),2):
        mono=max(-32768,min(32767,round((values[i]+values[i+1])/2)))
        centered.extend((mono,mono))
    with wave.open(str(path),'wb') as dst:
        dst.setnchannels(2);dst.setsampwidth(2);dst.setframerate(rate)
        dst.writeframes(struct.pack('<'+'h'*len(centered),*centered))
    print('Centered',path)
