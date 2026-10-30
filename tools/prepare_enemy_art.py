"""Prepare user-supplied frames, retaining originals and platform marks."""
from pathlib import Path
import numpy as np
import pygame

root=Path(__file__).resolve().parents[1]
dest=root/'Assets/Art/enemy_normal_v1'; dest.mkdir(parents=True,exist_ok=True)
states=('idle','walk_left','walk_right','attack_ready','attack_swing','attack_recover','hit','dead')
for state in states:
    src=Path('C:/Users/qiezh/Downloads')/f'normal_{state}.png.png'
    image=pygame.image.load(str(src))
    pixels=pygame.surfarray.array3d(image).astype(np.int16)
    # Only near-neutral bright background. Preserve silver armor and eyes.
    low=pixels.min(axis=2); chroma=pixels.max(axis=2)-low
    alpha=np.where((low>225)&(chroma<22),0,255).astype('uint8')
    result=pygame.Surface(image.get_size(),pygame.SRCALPHA)
    pygame.surfarray.blit_array(result,pixels.astype('uint8'))
    view=pygame.surfarray.pixels_alpha(result); view[:]=alpha; del view
    # Determine framing from the dark body, not pale footer/background noise.
    body=(low<185)&(alpha>0)
    xs,ys=np.where(body)
    bounds=pygame.Rect(max(0,int(xs.min())-3),max(0,int(ys.min())-3),
                       min(image.get_width(),int(xs.max())+4)-max(0,int(xs.min())-3),
                       min(image.get_height(),int(ys.max())+4)-max(0,int(ys.min())-3))
    crop=result.subsurface(bounds).copy()
    # Align all living states in a shared canvas, using the same body height.
    height=480 if state!='dead' else 190
    width=max(1,round(crop.get_width()*height/crop.get_height()))
    resized=pygame.transform.smoothscale(crop,(width,height))
    canvas=pygame.Surface((640,512),pygame.SRCALPHA)
    canvas.blit(resized,((640-width)//2,500-height))
    pygame.image.save(canvas,str(dest/(state+'.png')))
    print(state,width,height)
