from PIL import Image
from prepare_pixel_pack import ROOT,keyed,cells

def main():
    for name in ('spear','sword','bossfx'):
        path=ROOT/'source'/f'melee_v5_{name}.png'
        if not path.exists(): continue
        image=keyed(Image.open(path))
        if name=='spear':
            image.resize((256,256),Image.Resampling.LANCZOS).save(ROOT/'runtime'/'low_spear_idle.png')
        elif name=='sword':
            frames=cells(image,4,2)
            poses=('idle','windup','attack','followthrough','recover','guard','guard_hit','idle_end')
            for pose,frame in zip(poses,frames):
                frame=frame.crop((2,2,frame.width-2,frame.height-2))
                frame.resize((512,512),Image.Resampling.LANCZOS).save(ROOT/'runtime'/f'low_sword_{pose}.png')
        else:
            for key,frame in zip(('hammer','hunt','snipe','brood','duel','warning','stagger','death'),cells(image,4,2)):
                frame.resize((256,256),Image.Resampling.LANCZOS).save(ROOT/'runtime'/f'fx_signature_{key}.png')
        print('Imported',name)
if __name__=='__main__': main()
