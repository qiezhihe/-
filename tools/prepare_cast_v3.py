"""Import complete coherent casts; all states originate from one generated sheet."""
from PIL import Image, ImageDraw
from prepare_pixel_pack import ROOT, keyed, cells

def main():
    preview=Image.new('RGB',(1280,6*180),'#202634')
    draw=ImageDraw.Draw(preview)
    for row,unit in enumerate(('runner','normal','shooter','tank','elite','bat')):
        path=ROOT/'source'/f'cast_v3_{unit}.png'
        if not path.exists(): continue
        frames=cells(keyed(Image.open(path)),4,4)
        # Shared sheet transform, never stretch a fallen body to standing height.
        boxes=[f.getbbox() for f in frames]
        assert all(boxes),unit
        box=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
        scale=min(288/(box[2]-box[0]),288/(box[3]-box[1]))
        for i,f in enumerate(frames):
            crop=f.crop(box)
            crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
            canvas=Image.new('RGBA',(320,320))
            canvas.alpha_composite(crop,((320-crop.width)//2,304-crop.height))
            canvas.save(ROOT/'runtime'/f'anime_enemy_{unit}_cast3_{i}.png')
            if i in (0,2,4,6,8,9,10,12,14,15):
                col=(0,2,4,6,8,9,10,12,14,15).index(i)
                small=canvas.resize((128,128),Image.Resampling.LANCZOS)
                preview.paste(small,(col*128,row*180+24),small)
        draw.text((8,row*180+5),unit,fill='white')
        print('Complete cast imported:',unit)
    preview.save(ROOT.parents[2]/'artifacts'/'cast_v3_preview.png')

if __name__=='__main__': main()
