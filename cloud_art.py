"""Cached, alpha-keyed cloud-generated UI and equipment artwork."""
from pathlib import Path
import math
import pygame

class CloudArt:
    # First-person assets sit in the lower-right corner.  Keep a small inset
    # so the hand and weapon do not look detached from the viewport edge.
    WEAPON_RIGHT_INSET=8
    WEAPON_BOTTOM_INSET=8

    def __init__(self):
        self.images={}; self.cache={}
        self.low_frames={}
        folder=Path(__file__).parent/'Assets/Art/pixel_portal_v1/runtime'
        self.coherent_sword=(folder.parent/'source/melee_v5_sword.png').exists()
        self.melee_v7={name:(folder.parent/'source'/f'melee_v7_{name}.png').exists() for name in ('spear','sword')}
        for p in folder.glob('low_*.png'):
            frame=pygame.image.load(str(p)).convert_alpha()
            # Intentionally retain whitespace and original placement.
            self.low_frames[p.stem]=frame
        for p in folder.glob('*.png'):
            if not p.stem.startswith(('weapon_','pet_','icon_','fx_','prop_','player_')) and not p.stem.endswith('_frame'): continue
            im=pygame.image.load(str(p)).convert_alpha()
            rgb=pygame.surfarray.pixels3d(im); alpha=pygame.surfarray.pixels_alpha(im)
            if p.stem in ('fx_boss_slam','fx_boss_rupture'):
                # Legacy effects retain a dark magenta key fringe; enlarging
                # them to the real damage footprint must not enlarge that key.
                channels=rgb.astype('int16')
                r,g,b=channels[:,:,0],channels[:,:,1],channels[:,:,2]
                alpha[(r>g*1.35+12)&(b>g*1.35+12)]=0
            del rgb,alpha
            bounds=im.get_rect() if p.stem.startswith(('fx_story_','fx_entrance_')) else im.get_bounding_rect(min_alpha=128)
            self.images[p.stem]=im.subsurface(bounds).copy()
        for key in list(self.images):
            if key.startswith('anime_ui_') and key.endswith('_frame'):
                role=key[len('anime_ui_'):-len('_frame')]
                self.images[role+'_v2_frame']=self.images[key]
                if role=='boss': self.images['boss_frame']=self.images[key]
            elif key.startswith('icon_anime_'):
                self.images['icon_'+key[len('icon_anime_'):]]=self.images[key]

    def blit(self,surface,key,rect):
        if key.startswith('pet_') and '_motion_' not in key:
            candidate=key+'_motion_'+str((pygame.time.get_ticks()//120)%4)
            if candidate in self.images: key=candidate
        animated=key+'_'+str((pygame.time.get_ticks()//90)%4)
        if animated in self.images and key not in ('fx_boss_charge','fx_boss_slam'): key=animated
        if key not in self.images: return False
        rect=pygame.Rect(rect); cachekey=(key,rect.size)
        if cachekey not in self.cache:
            if len(self.cache)>=256: self.cache.pop(next(iter(self.cache)))
            source=self.images[key]
            if key.endswith('_frame'):
                # Nine-slice: keep border thickness instead of stretching knobs and corners.
                target=pygame.Surface(rect.size,pygame.SRCALPHA)
                edge=min(12,source.get_width()//4,source.get_height()//4,rect.width//3,rect.height//3)
                sx=(0,edge,source.get_width()-edge,source.get_width())
                sy=(0,edge,source.get_height()-edge,source.get_height())
                tx=(0,edge,rect.width-edge,rect.width); ty=(0,edge,rect.height-edge,rect.height)
                for row in range(3):
                    for col in range(3):
                        patch=source.subsurface((sx[col],sy[row],sx[col+1]-sx[col],sy[row+1]-sy[row]))
                        target.blit(pygame.transform.scale(patch,(tx[col+1]-tx[col],ty[row+1]-ty[row])),(tx[col],ty[row]))
                self.cache[cachekey]=target
            else:
                self.cache[cachekey]=pygame.transform.scale(source,rect.size)
        surface.blit(self.cache[cachekey],rect); return True

    def weapon(self,g):
        name=('smg','shotgun','mg','sniper','sword','boomerang','spear','dagger')[g.weapon_index]
        key='weapon_'+name
        if key not in self.images: return False
        w,h=g.screen.get_size(); melee=g.weapon_index>=4
        if name=='boomerang' and any(shot['kind']==name for shot in g.combat.throws):
            return True  # The weapon is in flight, not duplicated in the player's hand.
        recoil=max(0,min(1,(g.muzzle_until-g.now)/70))
        swing=max(0,min(1,(g.combat.cooldown-g.now)/max(1,g.fire_delay)))
        pose='idle'
        if melee:
            if swing>.65: pose='attack'
            elif swing>0: pose='recover'
        elif recoil>.4: pose='attack'
        elif recoil>0: pose='recover'
        held='held_'+name+'_'+pose
        age=g.now-getattr(g,'weapon_action_start',-100000)
        if melee:
            sequence=((.10,'windup'),(.30,'attack'),(.48,'followthrough'),(.72,'recover_mid'),(1,'recover'))
            fraction=age/max(1,g.fire_delay)
        else:
            sequence=((.22,'fire'),(.48,'recoil'),(.72,'recover_mid'),(1,'recover'))
            fraction=age/max(50,min(220,g.fire_delay))
        low_pose='idle'
        if 0<=fraction<1:
            low_pose=next(p for limit,p in sequence if fraction<limit)
        if low_pose=='recover_mid': low_pose='recover'
        if name=='spear':
            shot=next((shot for shot in g.combat.throws if shot['kind']=='spear'),None)
            if shot: low_pose='reach' if shot.get('returning') else 'empty'
        if melee and g.guarding: low_pose='guard'
        if not melee and g.reload_until:
            progress=(g.now-g.reload_start)/max(1,g.reload_duration)
            low_pose='reload_out' if progress<.4 else 'reload_in' if progress<.8 else 'bolt'
        low_key='low_'+name+'_'+low_pose
        if name in ('smg','shotgun','mg','sniper'):
            if g.reload_until:
                frame=8+min(7,int(max(0,min(.999,(g.now-g.reload_start)/max(1,g.reload_duration)))*8))
            elif 0<=fraction<1: frame=min(7,int(fraction*8))
            else: frame=None
            candidate='low_'+name+'_anim_'+str(frame)
            if frame is not None and candidate in self.low_frames: low_key=candidate
            # Idle is always the authored static pose. Do not let an old
            # animation frame containing a muzzle flash leak into the weapon
            # while the player is merely looking around.
            if not g.reload_until and not (g.muzzle_until>g.now):
                low_key='low_'+name+'_idle'
        elif name in ('dagger','boomerang') and 0<=fraction<1:
            candidate='low_'+name+'_anim_'+str(min(15,int(fraction*16)))
            if candidate in self.low_frames: low_key=candidate
        if name=='sword' and not g.guarding and 0<=fraction<1 and not self.coherent_sword:
            candidate='low_sword_anim_'+str(min(15,int(fraction*16)))
            if candidate in self.low_frames: low_key=candidate
        if name=='sword' and self.melee_v7['sword'] and not g.guarding and 0<=fraction<1:
            low_key='low_sword_anim_'+str(min(7,int(fraction*8)))
        if name=='spear':
            shot=next((s for s in g.combat.throws if s['kind']=='spear'),None)
            if shot:
                throw_age=max(0,(g.now-shot['start'])/1000)
                if throw_age<.25: frame=min(3,int(throw_age/.25*4))
                elif shot.get('returning'):
                    distance=math.hypot(shot['x']-g.player[0],shot['y']-g.player[1])
                    frame=10 if distance>2 else min(15,12+int((2-distance)*1.5))
                else: frame=4+min(3,int((throw_age-.25)/.18))
                if self.melee_v7['spear']:
                    if throw_age<.25: frame=min(5,int(throw_age/.25*6))
                    elif shot.get('returning'): frame=10 if distance>2 else min(15,11+int((2-distance)*2))
                    else: frame=7
                candidate='low_spear_anim_'+str(frame)
                if candidate in self.low_frames: low_key=candidate
        if name=='dagger' and low_pose=='idle' and 'low_dagger_anim_0' in self.low_frames:
            low_key='low_dagger_anim_0'
        if name in ('smg','mg') and not g.reload_until and f'low_{name}_v9_0' in self.low_frames:
            # All poses come from the same generated design sheet.
            pose=1 if g.muzzle_until>g.now else 2 if 0<=fraction<.65 else 3 if 0<=fraction<1 else 0
            low_key=f'low_{name}_v9_{pose}'
        if name=='mg' and 'low_mg_v11_0' in self.low_frames:
            if g.reload_until:
                progress=max(0,min(.999,(g.now-g.reload_start)/max(1,g.reload_duration)))
                pose=4+min(11,int(progress*12))
            else:
                pose=1 if g.muzzle_until>g.now else 2 if 0<=fraction<.65 else 3 if 0<=fraction<1 else 0
            low_key=f'low_mg_v11_{pose}'
        if name=='mg' and g.reload_until and all(f'low_mg_reload_v16_{i}' in self.low_frames for i in range(8)):
            # Reload takes precedence over idle / recoil, including an active
            # muzzle timer from the last shot in the magazine.
            progress=max(0,min(.999,(g.now-g.reload_start)/max(1,g.reload_duration)))
            low_key=f'low_mg_reload_v16_{min(7,int(progress*8))}'
        if name=='smg' and g.reload_until and 'low_smg_reload_v12_0' in self.low_frames:
            progress=max(0,min(.999,(g.now-g.reload_start)/max(1,g.reload_duration)))
            low_key=f'low_smg_reload_v12_{min(7,int(progress*8))}'
        if name=='sniper' and 'low_sniper_v13_0' in self.low_frames:
            if g.reload_until:
                progress=max(0,min(.999,(g.now-g.reload_start)/max(1,g.reload_duration)))
                pose=5+min(6,int(progress*7))
            else:
                pose=1 if g.muzzle_until>g.now else 2 if 0<=age<220 else 3 if 220<=age<500 else 4 if 500<=age<700 else 0
            low_key=f'low_sniper_v13_{pose}'
        if name=='sniper' and 'low_sniper_v14_0' in self.low_frames:
            if g.reload_until:
                progress=max(0,min(.999,(g.now-g.reload_start)/max(1,g.reload_duration)))
                pose=8+min(7,int(progress*8))
            else:
                cycle=max(70,min(700,g.fire_delay))
                # Never replay idle / muzzle frames partway through the bolt cycle.
                pose=2+min(4,int(age/cycle*5)) if 0<=age<cycle else 0
                if g.muzzle_until>g.now: pose=1
            low_key=f'low_sniper_v14_{pose}'
        if low_key not in self.low_frames: low_key='low_'+name+'_idle'
        if low_key in self.low_frames:
            overlay_size=(int(w*.36),int(h*.34))
            if name=='sniper' and low_key.startswith('low_sniper_v14_'):
                # The authored canvas is square; don't flatten the long rifle.
                overlay_size=(int(h*.45),int(h*.45))
            if name=='mg' and low_key.startswith('low_mg_reload_v16_'):
                overlay_size=(int(h*.45),int(h*.45))
            cachekey=(low_key,overlay_size)
            if cachekey not in self.cache:
                if len(self.cache)>=256: self.cache.pop(next(iter(self.cache)))
                self.cache[cachekey]=pygame.transform.scale(self.low_frames[low_key],overlay_size)
            frame=self.cache[cachekey]
            # Walking adds only a restrained camera/hand bob.  It is disabled
            # during reload so the authored hand positions remain readable.
            walking=bool(getattr(g,'walking',False)) and not g.reload_until
            phase=getattr(g,'walk_phase',0.0)
            sway_x=round(math.sin(phase)*2.5) if walking else 0
            sway_y=round(math.sin(phase*2.0)*1.5) if walking else 0
            sway_angle=math.sin(phase)*0.9 if walking else 0
            if sway_angle:
                frame=pygame.transform.rotate(frame,sway_angle)
            rect=frame.get_rect(bottomright=(w-self.WEAPON_RIGHT_INSET+sway_x,
                                               h-self.WEAPON_BOTTOM_INSET+sway_y))
            g.screen.blit(frame,rect)
            if g.reload_until and name in ('smg','mg'):
                progress=max(0,min(1,(g.now-g.reload_start)/max(1,g.reload_duration)))
                pygame.draw.rect(g.screen,(30,40,50),(w-240,h-48,210,5))
                pygame.draw.rect(g.screen,(80,220,200),(w-240,h-48,int(210*progress),5))
            return True
        if held in self.images: key=held
        # Preserve source aspect ratio, keep the aim corridor unobstructed.
        source=self.images[key]; target_h=150 if melee else 132
        target_w=min(250,round(target_h*source.get_width()/source.get_height()))
        frame=pygame.transform.smoothscale(source,(target_w,target_h))
        angle=0; dx=0; dy=int(recoil*9)
        if melee and swing:
            phase=math.sin(swing*math.pi)
            if g.weapon_index in (4,7): angle=-52*phase; dx=-int(72*phase)
            else: dy=int(72*phase); angle=16*phase
        if g.guarding and melee: angle=55; dx=-40
        if g.reload_until:
            phase=min(1,max(0,(g.now-g.reload_start)/g.reload_duration))
            angle=-25*math.sin(phase*math.pi); dy+=int(90*math.sin(phase*math.pi))
        frame=pygame.transform.rotate(frame,angle)
        bob_x=round(math.sin(getattr(g,'walk_phase',0))*2.5) if getattr(g,'walking',False) else 0
        bob_y=round(math.sin(getattr(g,'walk_phase',0)*2)*1.5) if getattr(g,'walking',False) else 0
        bob_angle=math.sin(getattr(g,'walk_phase',0))*.9 if getattr(g,'walking',False) else 0
        if bob_angle: frame=pygame.transform.rotate(frame,bob_angle)
        rect=frame.get_rect(bottomright=(w-self.WEAPON_RIGHT_INSET+bob_x,
                                          h-self.WEAPON_BOTTOM_INSET+bob_y))
        g.screen.blit(frame,rect)
        return True
