from PIL import Image
from prepare_pixel_pack import ROOT,keyed,cells
names=('1','2','3','4','5','6','7','headshot','melee')
for name,im in zip(names,cells(keyed(Image.open(ROOT/'source/kill_medals_v10.png')),3,3)):
 box=im.getbbox()
 if not box: raise ValueError(name)
 im=im.crop(box);im.thumbnail((112,112),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',(128,128));canvas.alpha_composite(im,((128-im.width)//2,(128-im.height)//2))
 canvas.save(ROOT/'runtime'/f'icon_kill_{name}.png')
print('Imported 9 generated kill medals')
