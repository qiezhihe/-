"""The generated boss sheet has unequal row heights; never slice it 4x5."""
from PIL import Image
from prepare_pixel_pack import ROOT,keyed

sheet=keyed(Image.open(ROOT/'source/combat_v9_bosses.png'))
rows=(0,313,537,785,1006,1254)
names=('colossus','hunter','judge','weaver','executioner')
for row,name in enumerate(names):
    frames=[sheet.crop((round(col*sheet.width/4),round(rows[row]*sheet.height/1254),
                        round((col+1)*sheet.width/4),round(rows[row+1]*sheet.height/1254)))
            for col in range(4)]
    boxes=[frame.getbbox() for frame in frames]
    scale=min(350/max(b[2]-b[0] for b in boxes),350/max(b[3]-b[1] for b in boxes))
    for pose,(frame,box) in enumerate(zip(frames,boxes)):
        frame=frame.crop(box)
        frame=frame.resize((round(frame.width*scale),round(frame.height*scale)),Image.Resampling.LANCZOS)
        canvas=Image.new('RGBA',(384,384))
        canvas.alpha_composite(frame,((384-frame.width)//2,376-frame.height))
        canvas.save(ROOT/'runtime'/f'anime_boss_{name}_v14_{pose}.png')
    print('Imported full silhouettes:',name)
