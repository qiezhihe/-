from PIL import Image
from prepare_pixel_pack import ROOT,keyed
def main():
 for name in ('smg','guard'):
  p=ROOT/'source'/f'low_v8_{name}.png'
  if not p.exists(): continue
  im=keyed(Image.open(p)).resize((512,512),Image.Resampling.LANCZOS)
  keys=('low_smg_idle','low_smg_idle_end') if name=='smg' else ('low_sword_guard','low_sword_guard_hit')
  for key in keys: im.save(ROOT/'runtime'/f'{key}.png')
  print('Imported',name)
if __name__=='__main__':main()
