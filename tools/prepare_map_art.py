"""Crop user supplied artwork; no generated substitute artwork."""
from pathlib import Path
import pygame

root=Path(__file__).resolve().parents[1]
out=root/'Assets'/'Art'/'map_v1'
out.mkdir(parents=True,exist_ok=True)
sources=[Path('C:/Users/qiezh/Downloads')/f'kling_20261006_作品_素材接在统一前缀后的_4613_{i}.png' for i in (0,1)]
images=[pygame.image.load(str(p)) for p in sources]
def crop(index,name,box,size):
    im=images[index]; w,h=im.get_size()
    rect=pygame.Rect(round(box[0]*w),round(box[1]*h),round((box[2]-box[0])*w),round((box[3]-box[1])*h))
    # Retain original crop pixels, rather than shrinking all art to 256px.
    asset=im.subsurface(rect).copy() if name not in ('menu','station') else pygame.transform.smoothscale(im.subsurface(rect),size)
    pygame.image.save(asset,str(out/(name+'.png')))
crop(0,'floor',(.063,.054,.276,.176),(256,256))
crop(0,'metal',(.741,.327,.925,.434),(256,256))
crop(0,'wall',(.020,.022,.291,.041),(512,128))
# Only molten material: dark banks must not masquerade as safe floor.
crop(0,'lava',(.762,.575,.827,.692),(256,256))
crop(1,'menu',(.0,.17,1,.495),(960,600))
crop(1,'station',(.375,.85,.626,.992),(256,256))
print('Saved',out)
