"""Raise the quiet supplied shotgun recording with a clipped-safe peak."""
from pathlib import Path
import wave, struct

path=Path(__file__).resolve().parents[1]/'Assets/audio/shotgun_shot.wav'
with wave.open(str(path),'rb') as src:
    channels,width,rate,frames,_,_=src.getparams(); raw=src.readframes(frames)
if width != 2: raise RuntimeError('Expected 16-bit PCM')
values=struct.unpack('<'+'h'*(frames*channels),raw)
peak=max(1,max(map(abs,values)))
target=30000
gain=min(7.0,target/peak)
out=[]
for sample in values:
    value=round(sample*gain)
    out.append(max(-32768,min(32767,value)))
with wave.open(str(path),'wb') as dst:
    dst.setnchannels(channels);dst.setsampwidth(width);dst.setframerate(rate)
    dst.writeframes(struct.pack('<'+'h'*len(out),*out))
print(f'Normalized {path.name}: peak {peak} -> {max(map(abs,out))}, gain {gain:.2f}x')
