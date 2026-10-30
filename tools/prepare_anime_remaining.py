"""Apply completed anime replacements last, keeping stable runtime keys."""
from PIL import Image
from prepare_pixel_pack import ROOT,keyed,cells,ICONS,WEAPONS
def save(im,key,size=None):
 if size: im=im.resize(size,Image.Resampling.LANCZOS)
 im.save(ROOT/'runtime'/(key+'.png'))
def main():
 for path in (ROOT/'source').glob('complete_*.png'):
  name=path.stem[9:]; im=Image.open(path)
  if name.startswith('weapon_'):
   weapon=name[7:]; frames=cells(keyed(im),4,4)
   for i,frame in enumerate(frames): save(frame,'low_'+weapon+'_anim_'+str(i),(256,256))
   gun=weapon in WEAPONS[:4]
   poses={'idle':0,'fire':1,'recoil':3,'recover':7,'reload_out':9,'reload_in':12,'bolt':14,'idle_end':0} if gun else {'idle':15 if weapon=='spear' else 0,'windup':2,'attack':5,'followthrough':7,'recover':11,'guard':0,'guard_hit':0,'idle_end':15,'empty':7,'reach':10,'catch':14}
   for pose,i in poses.items(): save(frames[i],'low_'+weapon+'_'+pose,(256,256))
   save(frames[poses['idle']],'weapon_'+weapon,(128,128))
  elif name=='idle_spear_ready':
   # Single generated ready-to-throw idle pose replaces only the spear idle;
   # throw, empty-hand and catch frames remain from the validated 4x4 sheet.
   save(keyed(im),'low_spear_idle',(256,256))
   save(keyed(im),'weapon_spear',(128,128))
  elif name.startswith('pet_'):
   from clean_pet_alpha import clean_pet
   pet=name[4:]; frames=cells(clean_pet(im),4,2)
   for i,frame in enumerate(frames): save(frame,'pet_'+pet+'_motion_'+str(i),(128,128))
   save(frames[0],'pet_'+pet,(128,128)); save(frames[4],'pet_'+pet+'_active',(128,128))
  elif name in ('props','effects','bossfx','signature','hybrid','motionfx'):
   labels={'props':('tree','grass','crystal','container','crate','spore','portal','console','reactor','tank','vent','tent'),
    'effects':('smg','shotgun','mg','sniper','slash','boomerang','spear','dash','bullet','orb','impact','shield','explosion','heal','danger','charge'),
    'bossfx':('warning','slam','charge','beam_hit','split','rupture','thruster','stagger'),
    'signature':('hammer','hunt','snipe','brood','duel','warning','stagger','death'),
    'hybrid':('field_medic','vampire_armor','mobile_gunner','critical_feed','toxic_fire','ice_breaker','siege_round','blast_master','survivalist','executioner','battle_scholar','quick_hands')}
   if name=='motionfx':
    for i,frame in enumerate(cells(keyed(im),4,4)):
     if i//4 in (1,2): continue  # Rejected: sheets contain female characters.
     save(frame,('fx_heal','fx_boss_charge','fx_boss_slam','fx_portal')[i//4]+'_'+str(i%4),(192,192))
   else:
    prefix={'props':'prop_','effects':'fx_','bossfx':'fx_boss_','signature':'fx_signature_','hybrid':'icon_'}[name]
    for label,frame in zip(labels[name],cells(keyed(im),4,len(labels[name])//4)): save(frame,prefix+label,(192,192))
  elif name=='menu': save(im.convert('RGB'),'menu',(960,600))
  elif name=='laser':
   import numpy as np
   data=np.array(im.convert('RGBA')); r,g,b=data[:,:,:3].transpose(2,0,1)
   data[(g>150)&(r<120)&(b<120)]=0
   save(Image.fromarray(data),'fx_laser',(256,24))
  else: save(keyed(im),{'portrait':'player_portrait','station':'station','wave':'fx_wave'}[name],(256,256))
 print('Anime replacements applied')
if __name__=='__main__': main()
