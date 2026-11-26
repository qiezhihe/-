"""Import the real generated atlas; its rows have measured, unequal margins."""
from pathlib import Path
import sys
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from weapon_evolutions import EVOLUTIONS


def main():
    folder=ROOT/'Assets/Art/pixel_portal_v1'
    sheet=Image.open(folder/'source/weapon_evolutions_v28.png').convert('RGBA')
    # The service returned a 1254-square atlas with cards in y=170..1084,
    # not square 512 cells. Keep each complete gold frame and weapon.
    rows=((170/1254,620/1254),(634/1254,1086/1254))
    for i,card in enumerate(EVOLUTIONS):
        top,bottom=rows[i//4]; col=i%4
        frame=sheet.crop((round(col*sheet.width/4),round(top*sheet.height),
                          round((col+1)*sheet.width/4),round(bottom*sheet.height)))
        frame=frame.resize((192,276),Image.Resampling.LANCZOS)
        frame.save(folder/'runtime'/('icon_'+card[0]+'.png'))
    print('Imported eight generated evolution card illustrations')


if __name__=='__main__':main()
