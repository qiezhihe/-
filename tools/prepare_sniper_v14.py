"""Keep aspect ratio, common scale and wrist placement across the entire sheet."""
from PIL import Image
from prepare_pixel_pack import ROOT,keyed,cells

frames=cells(keyed(Image.open(ROOT/'source/sniper_v14.png')),4,4)
boxes=[im.getbbox() for im in frames]
box=(min(b[0] for b in boxes),min(b[1] for b in boxes),
     max(b[2] for b in boxes),max(b[3] for b in boxes))
for i,im in enumerate(frames):
    im=im.crop(box)
    im.thumbnail((246,246),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(256,256))
    canvas.alpha_composite(im,((256-im.width)//2,248-im.height))
    canvas.save(ROOT/'runtime'/f'low_sniper_v14_{i}.png')
print('Imported 16 sniper poses')
