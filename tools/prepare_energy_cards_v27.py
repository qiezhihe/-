from PIL import Image
from prepare_pixel_pack import keyed,cells,ROOT

sheet=keyed(Image.open(ROOT/'source/energy_cards_v27.png'))
for key,frame in zip(('stamina_core','stamina_regen','sprint_efficiency','blink_efficiency'),cells(sheet,4,1)):
    box=frame.getbbox(); frame=frame.crop(box) if box else frame
    frame.thumbnail((88,88),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(96,96)); canvas.alpha_composite(frame,((96-frame.width)//2,(96-frame.height)//2))
    canvas.save(ROOT/'runtime'/f'icon_anime_{key}.png')
print('Imported four energy icons')
