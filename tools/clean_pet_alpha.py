"""Pet-specific chroma removal including dark pink shadows and resize fringes."""
from PIL import Image, ImageFilter, ImageDraw
import numpy as np
from prepare_pixel_pack import ROOT, cells

def clean_pet(image):
    data=np.array(image.convert('RGBA'))
    r,g,b=data[:,:,:3].astype(np.int16).transpose(2,0,1)
    # Source sheets have shaded pink, not uniform bright #ff00ff.
    # Keep ivory, gray metal, green hair and orange skill effects intact.
    pink=(r>g*1.45+16)&(b>g*1.25+12)&(r>55)&(b>30)
    data[pink]=0
    image=Image.fromarray(data)
    return image

def main():
    preview=Image.new('RGB',(800,5*180),'#182c38')
    draw=ImageDraw.Draw(preview)
    for row,unit in enumerate(('healer','taunter','gunner','minelayer','berserker')):
        path=ROOT/'source'/f'complete_pet_{unit}.png'
        if not path.exists(): continue
        frames=cells(Image.open(path),4,2)
        for i,frame in enumerate(frames):
            frame=clean_pet(frame).resize((128,128),Image.Resampling.LANCZOS)
            data=np.array(frame)
            # Remove tiny transparent-edge resampling residue.
            data[data[:,:,3]<20]=0
            frame=Image.fromarray(data)
            frame.save(ROOT/'runtime'/f'pet_{unit}_motion_{i}.png')
            if i in (0,4):
                frame.save(ROOT/'runtime'/f'pet_{unit}{"_active" if i==4 else ""}.png')
            if i<4:
                small=frame.resize((160,160),Image.Resampling.NEAREST)
                preview.paste(small,(i*200,row*180+20),small)
        draw.text((4,row*180+4),unit,fill='white')
        print('Cleaned:',unit,'10 sprites')
    preview.save(ROOT.parents[2]/'artifacts'/'pets_alpha_preview.png')

if __name__=='__main__': main()
