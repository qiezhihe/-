from pathlib import Path
from PIL import Image
from prepare_pixel_pack import keyed,cells,ROOT
for kind,cols,rows in [('guns',4,2),('bosses',4,5)]:
 frames=cells(keyed(Image.open(ROOT/'source'/f'combat_v9_{kind}.png')),cols,rows)
 for row in range(rows):
  group=frames[row*4:row*4+4]; boxes=[im.getbbox() for im in group]
  box=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
  for col,im in enumerate(group):
   cut=im.crop(box); cut.thumbnail((246,246) if kind=='guns' else (350,350),Image.Resampling.LANCZOS)
   size=256 if kind=='guns' else 384
   canvas=Image.new('RGBA',(size,size));canvas.alpha_composite(cut,((size-cut.width)//2,size-cut.height-8))
   name=('smg','mg')[row] if kind=='guns' else ('colossus','hunter','judge','weaver','executioner')[row]
   key=f'low_{name}_v9_{col}' if kind=='guns' else f'anime_boss_{name}_v9_{col}'
   canvas.save(ROOT/'runtime'/f'{key}.png')
print('Imported coherent weapon and boss sequences')

