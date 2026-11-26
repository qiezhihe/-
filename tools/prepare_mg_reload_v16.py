"""Import eight generated reload poses without stretching tall source cells."""
from PIL import Image
from prepare_pixel_pack import ROOT, keyed, cells

frames=cells(keyed(Image.open(ROOT/'source/mg_reload_v16.png')),4,2)
# Remove thin generated panel seams at cell edges, not the weapon silhouette.
frames=[frame.crop((2,2,frame.width-2,frame.height-2)) for frame in frames]
boxes=[frame.getbbox() for frame in frames]
assert all(boxes),'Empty reload cell'
box=(min(b[0] for b in boxes),min(b[1] for b in boxes),
     max(b[2] for b in boxes),max(b[3] for b in boxes))
for index,frame in enumerate(frames):
    frame=frame.crop(box)
    frame.thumbnail((246,246),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(256,256))
    # Gun stock stays at the same right-hand anchor throughout the action.
    canvas.alpha_composite(frame,(248-frame.width,248-frame.height))
    canvas.save(ROOT/'runtime'/f'low_mg_reload_v16_{index}.png')
print('Imported eight machinegun reload frames')
