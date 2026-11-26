"""Import one generated, coherent machinegun sheet with a shared canvas."""
from PIL import Image
from prepare_pixel_pack import ROOT, keyed, cells

frames=cells(keyed(Image.open(ROOT/'source/mg_full_v11.png')),4,4)
boxes=[frame.getbbox() for frame in frames]
box=(min(b[0] for b in boxes),min(b[1] for b in boxes),
     max(b[2] for b in boxes),max(b[3] for b in boxes))
for index,frame in enumerate(frames):
    frame=frame.crop(box)
    frame.thumbnail((246,246),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(256,256))
    canvas.alpha_composite(frame,((256-frame.width)//2,248-frame.height))
    canvas.save(ROOT/'runtime'/f'low_mg_v11_{index}.png')
print('Imported 16 machinegun frames')
