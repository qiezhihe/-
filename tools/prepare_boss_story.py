from PIL import Image
from prepare_pixel_pack import ROOT,cells

def main():
    for name in ('colossus','hunter','judge','weaver','executioner'):
        path=ROOT/'source'/f'story_v1_{name}.png'
        if not path.exists(): continue
        for i,frame in enumerate(cells(Image.open(path).convert('RGB'),2,3)):
            # Preserve composition: generated panels may be square rather
            # than wide, so letterbox instead of stretching the characters.
            frame=frame.crop((2,2,frame.width-2,frame.height-2))
            frame.thumbnail((960,480),Image.Resampling.LANCZOS)
            canvas=Image.new('RGB',(960,480),(5,6,12))
            canvas.paste(frame,((960-frame.width)//2,(480-frame.height)//2))
            canvas.save(ROOT/'runtime'/f'fx_story_{name}_{i}.png')
        print('Story imported:',name)
if __name__=='__main__': main()
