"""Slice generated sheets into compact runtime sprites; sources are never modified."""
from pathlib import Path
from PIL import Image, ImageFilter
import numpy as np

ROOT=Path(__file__).resolve().parents[1]/'Assets/Art/pixel_portal_v1'
STATES=('idle','walk_left','walk_right','attack_ready','attack_swing','attack_recover','hit','dead')
WEAPONS=('smg','shotgun','mg','sniper','sword','boomerang','spear','dagger')
ICONS=('health','regen','shield','armor','speed','crit','critpower','magazine','reload','haste','pierce','pellets','shot_tight','mg_power','sniper_power','melee_power','sword_arc','melee_sustain','melee_guard','melee_stagger','boomerang_return','spear_pierce','dagger_dash','blue_supply','orange_reset','pet_healer','pet_taunter','pet_gunner','pet_minelayer','pet_berserker','xp','burn')

def keyed(im):
    data=np.array(im.convert('RGBA'))
    r,g,b=data[:,:,:3].astype(np.int16).transpose(2,0,1)
    background=(r>150)&(b>150)&(g<100)&(np.minimum(r,b)>g*1.6)
    # Remove dark antialiased key colour only beside the known background.
    # Interior purple details are not part of this narrow fringe mask.
    nearby=np.array(Image.fromarray(background.astype('uint8')*255).filter(ImageFilter.MaxFilter(5)))>0
    fringe=nearby&(r>g*1.3+12)&(b>g*1.3+12)
    data[background|fringe]=0
    dark=(data[:,:,0]<28)&(data[:,:,1]<28)&(data[:,:,2]<28)&(data[:,:,3]>0)
    border=np.zeros(dark.shape,dtype=bool); border[0,:]=border[-1,:]=border[:,0]=border[:,-1]=True
    flood=dark & border
    for _ in range(max(im.size)):
        grown=flood.copy(); grown[1:,:]|=flood[:-1,:]; grown[:-1,:]|=flood[1:,:]; grown[:,1:]|=flood[:,:-1]; grown[:,:-1]|=flood[:,1:]; grown &= dark
        if np.array_equal(grown,flood): break
        flood=grown
    data[flood]=0
    return Image.fromarray(data)

def cells(im,cols,rows):
    return [im.crop((round(c*im.width/cols),round(r*im.height/rows),round((c+1)*im.width/cols),round((r+1)*im.height/rows))) for r in range(rows) for c in range(cols)]

def save(im,name,size=None):
    if size: im=im.resize(size,Image.Resampling.NEAREST)
    im.save(ROOT/'runtime'/(name+'.png'))

def main():
    (ROOT/'runtime').mkdir(parents=True,exist_ok=True)
    for path in (ROOT/'source').glob('*.png'):
        name=path.stem; im=Image.open(path)
        if name.startswith(('locomotion_v2_','cast_v3_','idle_clean_v4_','melee_v5_','story_v1_','smg_v6_','melee_v7_','low_v8_')): continue
        if name.startswith('complete_'): continue
        if name.startswith('entrance_'):
            for i,frame in enumerate(cells(im.convert('RGB'),2,4)):
                save(frame,'fx_'+name+'_'+str(i),(960,480))
            continue
        if name.startswith('boss_ammo_'):
            frame=keyed(im); bounds=frame.getbbox()
            save(frame.crop(bounds) if bounds else frame,'fx_'+name,(192,192))
            continue
        if name.startswith('anime_enemy_'):
            for state,frame in zip(STATES,cells(keyed(im),4,2)): save(frame,name+'_'+state,(320,320))
            continue
        if name.startswith('anime_boss_'):
            for i,frame in enumerate(cells(keyed(im),4,4)):
                save(frame,name+'_motion_'+str(i),(384,384))
            continue
        if name=='anime_intro':
            data=np.array(keyed(im)); r,g,b=data[:,:,:3].astype(float).transpose(2,0,1)
            mask=(r>120)&(b>60)&(r>g*1.8+20)&(b>g*1.25+15)
            data[mask]=0
            for i,frame in enumerate(cells(Image.fromarray(data),4,2)): save(frame,'fx_anime_intro_'+str(i),(384,384))
            continue
        if name.startswith('anime_ui_'):
            frame=keyed(im); bounds=frame.getbbox()
            save(frame.crop(bounds) if bounds else frame,name+'_frame')
            continue
        if name=='anime_icons':
            for key,frame in zip(ICONS,cells(keyed(im),8,4)): save(frame,'icon_anime_'+key,(96,96))
            continue
        if name in ('held_sword','held_spear') and (ROOT/'source'/(name+'_v2.png')).exists(): continue
        if name.startswith('boss_cast_'):
            frames=cells(keyed(im),4,2)
            if name=='boss_cast_fx':
                labels=('hammer','hunt','snipe','brood','duel','warning','stagger','death')
                for label,frame in zip(labels,frames): save(frame,'fx_signature_'+label,(256,256))
            else:
                for state,frame in zip(STATES,frames): save(frame,name+'_'+state,(384,384))
            continue
        if name in ('held_sword_v2','held_spear_v2'):
            weapon='sword' if name=='held_sword_v2' else 'spear'
            frames=cells(keyed(im),4,2)
            poses=('idle','windup','attack','followthrough','recover','guard','guard_hit','idle_end') if weapon=='sword' else ('idle','windup','attack','followthrough','empty','reach','catch','idle_end')
            for pose,frame in zip(poses,frames): save(frame,'low_'+weapon+'_'+pose,(256,256))
            save(frames[0],'weapon_'+weapon,(128,128))
            continue
        if name=='held_shotgun_v2':
            for pose,frame in zip(('idle','pump','fire','recoil','recover','reload_out','reload_in','idle_end'),cells(keyed(im),4,2)):
                save(frame,'low_shotgun_'+pose,(256,256))
            save(cells(keyed(im),4,2)[0],'weapon_shotgun',(128,128)); continue
        if name=='held_spear_v3':
            for i,frame in enumerate(cells(keyed(im),4,4)): save(frame,'low_spear_anim_'+str(i),(256,256))
            continue
        if name.startswith('motion_enemy_'):
            unit=name[len('motion_enemy_'):]
            for i,frame in enumerate(cells(keyed(im),4,4)):
                save(frame,unit+'_motion_'+str(i),(256,256))
        elif name.startswith('motion_pet_'):
            unit=name[len('motion_pet_'):]
            for i,frame in enumerate(cells(keyed(im),4,2)):
                save(frame,'pet_'+unit+'_motion_'+str(i),(128,128))
        elif name.startswith('anim16_'):
            for i,frame in enumerate(cells(keyed(im),4,4)):
                save(frame,'low_'+name[7:]+'_anim_'+str(i),(256,256))
        elif name.startswith('enemy_'):
            frames=cells(keyed(im),4,2)
            # Common canvas and scale keep pose changes from changing body size.
            for state,frame in zip(STATES,frames):
                save(frame,name[6:]+'_'+state,(256,256))
        elif name.startswith('held_'):
            frames=cells(keyed(im),4,2)
            poses=('idle','fire','recoil','recover','reload_out','reload_in','bolt','idle_end') if name[5:] in WEAPONS[:4] else ('idle','windup','attack','followthrough','recover','guard','guard_hit','idle_end')
            for pose,frame in zip(poses,frames): save(frame,'low_'+name[5:]+'_'+pose,(256,256))
            save(frames[0], 'weapon_'+name[5:],(128,128))
        elif name=='pets':
            for i,frame in enumerate(cells(keyed(im),5,2)):
                save(frame,'pet_'+('healer','taunter','gunner','minelayer','berserker')[i%5]+('_active' if i>=5 else ''),(128,128))
        elif name=='hybrid_icons':
            names=('field_medic','vampire_armor','mobile_gunner','critical_feed','toxic_fire','ice_breaker','siege_round','blast_master','survivalist','executioner','battle_scholar','quick_hands')
            for key,frame in zip(names,cells(keyed(im),4,3)): save(frame,'icon_'+key,(64,64))
        elif name=='motion_ui_v3':
            for i,frame in enumerate(cells(keyed(im),4,4)):
                save(frame,('fx_heal','fx_boss_charge','fx_boss_slam','fx_portal')[i//4]+'_'+str(i%4),(192,192))
        elif name=='icons':
            for key,frame in zip(ICONS,cells(keyed(im),8,4)): save(frame,'icon_'+key,(64,64))
        elif name=='effects':
            names=('smg','shotgun','mg','sniper','slash','boomerang','spear','dash','bullet','orb','impact','shield','explosion','heal','danger','charge')
            for key,frame in zip(names,cells(keyed(im),4,4)): save(frame,'fx_'+key,(96,96))
        elif name=='props':
            names=('tree','grass','crystal','container','crate','spore','portal','console','reactor','tank','vent','tent')
            for key,frame in zip(names,cells(keyed(im),4,3)): save(frame,'prop_'+key,(192,192))
        elif name=='ui':
            # This sheet uses unequal horizontal allocations; inspect-derived bounds.
            boxes=((0,.06,.47,.48),(.48,.06,.71,.48),(.72,.06,1,.48),
                   (0,.55,.38,.84),(.38,.63,.72,.75),(.73,.55,1,.84))
            frames=[keyed(im).crop(tuple(round(v*(im.width if i%2==0 else im.height)) for i,v in enumerate(box))) for box in boxes]
            for key,frame in zip(('hud','card','slot','pet','boss','pause'),frames):
                bounds=frame.getbbox()
                save(frame.crop(bounds) if bounds else frame,key+'_frame')
        elif name=='ui_v2':
            names=('hud_v2','card_v2','slot_v2','pet_v2','ammo_v2','pause_v2','objective_v2','wave_v2')
            for key,frame in zip(names,cells(keyed(im),4,2)):
                bounds=frame.getbbox(); save(frame.crop(bounds) if bounds else frame,key+'_frame')
        elif name=='menu': save(im.convert('RGB'),name,(960,600))
        elif name=='boss_souls_fx':
            for key,frame in zip(('warning','slam','charge','beam_hit','split','rupture','thruster','stagger'),cells(keyed(im),4,2)):
                save(frame,'fx_boss_'+key,(192,192))
        elif name=='boss_header_v2':
            frame=keyed(im); bounds=frame.getbbox()
            save(frame.crop(bounds) if bounds else frame,'boss_frame')
        elif name=='fx_wave': save(keyed(im),name,(96,96))
        elif name=='fx_laser':
            image=im.convert('RGBA'); data=image.load()
            for y in range(image.height):
                for x in range(image.width):
                    r,g,b,a=data[x,y]
                    if g>150 and r<120 and b<120: data[x,y]=(0,0,0,0)
            bounds=image.getbbox()
            save(image.crop(bounds) if bounds else image,name,(256,24))
        elif name in ('station','player_portrait'): save(keyed(im),name,(256,256))
        elif name=='weapon_crate_views':
            frames=cells(keyed(im),2,2)
            for key,frame in zip(('front','side','top','threequarter'),frames): save(frame,'crate_'+key,(256,192))
        else: save(im.convert('RGB'),name,(128,128))
    from prepare_anime_remaining import main as apply_anime
    apply_anime()
    from prepare_locomotion_v2 import main as apply_locomotion
    apply_locomotion()
    from prepare_cast_v3 import main as apply_cast
    apply_cast()
    from prepare_gun_idle import main as apply_gun_idle
    apply_gun_idle()
    from prepare_melee_v5 import main as apply_melee
    apply_melee()
    from prepare_boss_story import main as apply_story
    apply_story()
    from prepare_melee_v7 import main as apply_melee_v7
    apply_melee_v7()
    from prepare_low_v8 import main as apply_low_v8
    apply_low_v8()
    print('Runtime sprites:',len(list((ROOT/'runtime').glob('*.png'))))

if __name__=='__main__': main()
