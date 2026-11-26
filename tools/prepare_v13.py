from PIL import Image
from prepare_pixel_pack import ROOT,keyed,cells

for name,cols,rows in [('sniper',4,3),('pet_skills',5,2)]:
    path=ROOT/'source'/f'{name}_v13.png'
    if not path.exists(): continue
    frames=cells(keyed(Image.open(path)),cols,rows)
    for i,frame in enumerate(frames):
        if name=='sniper':
            key=f'low_sniper_v13_{i}'
        else:
            key='fx_pet_v13_'+('healer','taunter','gunner','minelayer','berserker')[i%5]+'_'+str(i//5)
        frame.resize((256,256),Image.Resampling.LANCZOS).save(ROOT/'runtime'/f'{key}.png')
    print('Imported',name,len(frames))
