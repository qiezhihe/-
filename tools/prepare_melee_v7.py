"""Authoritative coherent spear and shield/saber sprites, imported last."""
from PIL import Image
from prepare_pixel_pack import ROOT,keyed,cells

def main():
    for weapon in ('spear','sword'):
        path=ROOT/'source'/f'melee_v7_{weapon}.png'
        if not path.exists(): continue
        frames=cells(keyed(Image.open(path)),4,4)
        frames=[f.crop((2,2,f.width-2,f.height-2)).resize((512,512),Image.Resampling.LANCZOS) for f in frames]
        mapping=({'idle':0,'windup':3,'attack':4,'followthrough':5,'empty':7,'reach':10,'catch':11,'recover':14,'guard':0,'idle_end':15}
                 if weapon=='spear' else {'idle':0,'windup':2,'attack':4,'followthrough':5,'recover':6,'guard':12,'guard_hit':13,'idle_end':15})
        for i,frame in enumerate(frames): frame.save(ROOT/'runtime'/f'low_{weapon}_anim_{i}.png')
        for pose,i in mapping.items(): frames[i].save(ROOT/'runtime'/f'low_{weapon}_{pose}.png')
        frames[0].resize((128,128),Image.Resampling.LANCZOS).save(ROOT/'runtime'/f'weapon_{weapon}.png')
        print('Imported coherent v7:',weapon)
if __name__=='__main__': main()
