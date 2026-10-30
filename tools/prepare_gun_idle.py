"""Apply generated unlit gun idle after animation sheets are imported."""
from PIL import Image
from prepare_pixel_pack import ROOT,keyed

def main():
    for gun in ('smg','mg','sniper'):
        source=ROOT/'source'/f'idle_clean_v4_{gun}.png'
        if gun=='smg' and (ROOT/'source'/'smg_v6_idle.png').exists():
            source=ROOT/'source'/'smg_v6_idle.png'
        if not source.exists(): continue
        image=keyed(Image.open(source))
        image=image.resize((256,256),Image.Resampling.LANCZOS)
        for pose in ('idle','idle_end'):
            image.save(ROOT/'runtime'/f'low_{gun}_{pose}.png')
        image.resize((128,128),Image.Resampling.LANCZOS).save(ROOT/'runtime'/f'weapon_{gun}.png')
        print('Imported unlit idle:',gun)

if __name__=='__main__': main()
