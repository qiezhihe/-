"""Import generated frontal eight-frame cycles without touching combat poses."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
from prepare_pixel_pack import ROOT, keyed, cells

def main():
    preview = Image.new('RGB', (1024, 6 * 160), '#202634')
    draw = ImageDraw.Draw(preview)
    for row, unit in enumerate(('runner', 'elite', 'normal', 'shooter', 'tank', 'bat')):
        path = ROOT / 'source' / f'locomotion_v2_{unit}.png'
        if (ROOT/'source'/f'cast_v3_{unit}.png').exists(): continue
        if not path.exists():
            print('Pending:', unit)
            continue
        frames = cells(keyed(Image.open(path)), 4, 2)
        # One shared transform per sheet preserves leg and wing movement.
        boxes = [frame.getbbox() for frame in frames]
        if any(box is None for box in boxes):
            raise ValueError(f'Empty generated cell: {unit}')
        box = (min(b[0] for b in boxes), min(b[1] for b in boxes),
               max(b[2] for b in boxes), max(b[3] for b in boxes))
        scale = min(288 / (box[2]-box[0]), 288 / (box[3]-box[1]))
        for i, frame in enumerate(frames):
            crop = frame.crop(box)
            crop = crop.resize((round(crop.width*scale), round(crop.height*scale)), Image.Resampling.LANCZOS)
            canvas = Image.new('RGBA', (320, 320))
            canvas.alpha_composite(crop, ((320-crop.width)//2, 304-crop.height))
            canvas.save(ROOT / 'runtime' / f'anime_enemy_{unit}_locomotion_{i}.png')
            small = canvas.resize((128,128), Image.Resampling.LANCZOS)
            preview.paste(small, (i*128, row*160+24), small)
        draw.text((8,row*160+5),unit,fill='white')
        print('Imported:', unit, '8 frames')
    target = ROOT.parents[2] / 'artifacts' / 'locomotion_v2_preview.png'
    preview.save(target)
    print('Preview:', target)

if __name__ == '__main__': main()
