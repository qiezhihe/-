from pathlib import Path
import pygame

class EnemyArt:
    def __init__(self):
        folder=Path(__file__).parent/'Assets/Art/pixel_portal_v1/runtime'
        self.frames={p.stem[7:]:pygame.image.load(str(p)).convert_alpha() for p in folder.glob('normal_*.png')}
        self.cloud={p.stem:pygame.image.load(str(p)).convert_alpha() for p in folder.glob('*.png') if p.stem.startswith(('bat_','runner_','shooter_','tank_','elite_','boss_','anime_boss_','anime_enemy_')) and not p.stem.endswith('_frame')}
        for unit in ('normal','runner','shooter','tank','elite','bat'):
            prefix='anime_enemy_'+unit
            if prefix+'_cast3_8' in self.cloud:
                for state,index in {'idle':8,'walk_left':0,'walk_right':4,'attack_ready':9,'attack_swing':10,'attack_recover':11,'hit':12,'dead':15}.items():
                    self.cloud[prefix+'_'+state]=self.cloud[f'{prefix}_cast3_{index}']
        self.cache={}
        self.positions={}
        self.anchors={}
        # Find physical foot rows once on tiny source sprites. Scanning every
        # pixel of a 2048px attack pose in Python caused first-use stalls.
        self.boss_source_anchors={}
        for name,im in self.cloud.items():
            if not name.startswith(('anime_boss_','boss_cast_','boss_fan','boss_dash')): continue
            import numpy as np
            alpha=pygame.surfarray.array_alpha(im)
            counts=(alpha[im.get_width()//4:im.get_width()*3//4,:]>127).sum(axis=0)
            rows=np.flatnonzero(counts>max(2,im.get_width()//20))
            self.boss_source_anchors[name]=(int(rows[-1])+1 if len(rows) else im.get_bounding_rect(min_alpha=128).bottom)/im.get_height()

    def state(self,g,e):
        if e[2]<=0: return 'dead'
        if e[3]>g.now: return 'hit'
        animation=g.attack_animations.get(id(e))
        if animation:
            kind,end=animation
            if kind=='melee' and g.now<end: return 'attack_ready'
            if kind=='swing' and g.now<end:
                return 'attack_swing' if end-g.now>90 else 'attack_recover'
        if e[2]<=0: return 'dead'
        if e[3]>g.now: return 'hit'
        motion=getattr(g,'_enemy_motion',{}).get(id(e))
        if motion and 0<=g.now-motion[1]<=100: return 'walk_left'
        return 'idle'

    def visual(self,g,e,sx,size,state=None):
        state=state or self.state(g,e)
        prefix={'bat':'bat','runner':'runner','shooter':'shooter','tank':'tank','elite':'elite','boss':('boss_fan','boss_dash','boss_ring')[(g.wave//5-1)%3]}.get(e[5],'normal')
        if e[5]=='boss':
            new_prefix='boss_cast_'+('colossus','hunter','judge','weaver','executioner')[(g.wave//5-1)%5]
            if new_prefix+'_idle' in self.cloud: prefix=new_prefix
            pattern=g.combat.boss_pattern.get(id(e))
            if pattern and state not in ('dead','hit'):
                state='attack_ready' if g.now<pattern['windup'] else 'attack_swing' if g.now<pattern['impact'] else 'attack_recover'
            anime='anime_boss_'+('colossus','hunter','judge','weaver','executioner')[(g.wave//5-1)%5]
            if anime+'_motion_0' in self.cloud:
                prefix=anime
        source=self.cloud if prefix!='normal' else self.frames
        replacement='anime_enemy_'+e[5]
        if e[5]!='boss' and replacement+'_idle' in self.cloud:
            prefix=replacement; source=self.cloud
        frame_key=f'{prefix}_{state}'
        if prefix.startswith('anime_boss_'): frame_key=prefix+'_motion_0'
        if frame_key not in source: frame_key=f'{prefix}_idle'
        if frame_key not in source: source=self.frames; frame_key=state
        if source is self.frames: frame_key=state
        motion=int(g.now//110+e[0])%4
        animation=g.attack_animations.get(id(e))
        if e[3]>g.now: motion=int(g.now//110+e[0])%4
        elif animation and animation[1]>g.now:
            duration=350 if animation[0]=='melee' else 180
            elapsed=max(0,duration-(animation[1]-g.now))
            motion=(4 if animation[0]=='melee' else 8)+min(3,int(elapsed/duration*4))
        pattern=g.combat.boss_pattern.get(id(e))
        if pattern and g.now<pattern['windup']: motion=4+min(3,int(max(0,1-(pattern['windup']-g.now)/1100)*4))
        candidate=(prefix+'_' if source is self.cloud else '')+'motion_'+str(motion)
        if state in ('idle','walk_left','walk_right') and candidate in source and not prefix.startswith('anime_enemy_'): frame_key=candidate
        # Generated enemy sheets use named poses. Never replace them with the
        # legacy four-frame motion cycle, which caused visible stride jumps.
        if prefix.startswith('anime_enemy_') and state in ('walk_left','walk_right'):
            frame_key=prefix+'_'+state
        if e[5]=='bat' and prefix.startswith('anime_enemy_'):
            # The bat sheet's named frames are a wing flap cycle; keep its
            # center fixed instead of applying ground-walk timing.
            frame_key=prefix+('_walk_left' if int(g.now//120)%2==0 else '_walk_right') if state not in ('dead','hit') else prefix+'_'+state
        # Generated frontal cycles keep facing the player: eight distinct
        # foot-contact / passing poses, or eight wing articulation poses.
        if prefix.startswith('anime_enemy_') and state in ('idle','walk_left','walk_right'):
            cycle = int(g.now // (140 if e[5]=='bat' else 190)) % 8
            candidate = f'{prefix}_locomotion_{cycle}'
            if candidate in source:
                frame_key = candidate
        if prefix.startswith('anime_enemy_') and prefix+'_cast3_8' in source:
            pose={'idle':8,'attack_ready':9,'attack_swing':10,'attack_recover':11,'hit':12,'dead':15}.get(state,8)
            if state in ('walk_left','walk_right'):
                distance=getattr(g,'_enemy_motion',{}).get(id(e))
                pose=(int(distance[0]/.18)%8 if distance and e[5]!='bat'
                      else int(g.now//(140 if e[5]=='bat' else 190))%8)
            if e[5]=='bat' and state=='idle': pose=int(g.now//140)%8
            frame_key=f'{prefix}_cast3_{pose}'
        if prefix.startswith('anime_boss_'):
            frame=int(g.now//80)%4
            if state=='dead': frame=15
            elif pattern:
                if g.now<pattern['windup']: frame=4+min(3,int(max(0,1-(pattern['windup']-g.now)/1100)*4))
                elif g.now<pattern['impact']: frame=8+min(2,int((g.now-pattern['windup'])/100))
                else: frame=11
            frame_key=prefix+'_motion_'+str(frame)
        if e[5]=='boss' and prefix+'_v9_0' in source and state!='dead':
            pose=0
            if pattern:
                pose=0 if g.now<pattern['windup'] else 1 if g.now<pattern['impact'] else 2
                if pattern.get('skill')=='laser' and pattern['windup']<=g.now<pattern['impact']: pose=3
            frame_key=f'{prefix}_v9_{pose}'
        # Shared canvas alignment means pose changes cannot move the feet.
        factor=4.6 if e[5]=='boss' else .65 if e[5]=='bat' else 1.3
        height=max(16,min(2048 if e[5]=='boss' else 1024,round(size*factor/16)*16)); width=height
        key=(frame_key,height)
        if key not in self.cache:
            if len(self.cache)>384: self.cache.pop(next(iter(self.cache)))
            self.cache[key]=pygame.transform.scale(source[frame_key],(width,height))
        image=self.cache[key]
        if e[5]!='boss' and e[3]-g.now>100:
            image=image.copy()
            image.fill((65,45,15,0),special_flags=pygame.BLEND_RGBA_ADD)
        depth=(e[0]-g.player[0])*__import__('math').cos(g.angle)+(e[1]-g.player[1])*__import__('math').sin(g.angle)
        zoom=2.5 if g.ads and g.weapon_index==3 else 1.4 if g.ads else 1
        feet=g.screen.get_height()/2+g.pitch*g.screen.get_height()*.72+(g.z+.5)/depth*g.screen.get_height()*.55*zoom
        pattern=g.combat.boss_pattern.get(id(e),{})
        if pattern.get('skill')=='slam' and pattern['windup']<=g.now<pattern['impact']:
            import math
            phase=(g.now-pattern['windup'])/(pattern['impact']-pattern['windup'])
            feet-=math.sin(phase*math.pi)*1.8/depth*g.screen.get_height()*.55*zoom
        if e[5]=='bat': feet-=.85/depth*g.screen.get_height()*.55*zoom
        elif e[5]=='boss' and prefix=='boss_ring': feet-=.18/depth*g.screen.get_height()*.55*zoom
        bounds=image.get_bounding_rect(min_alpha=128)
        rect=image.get_rect()
        # Ignore airborne particles when choosing the physical foot baseline.
        anchor=bounds.bottom
        if '_locomotion_' in frame_key or '_cast3_' in frame_key:
            # Fixed canvas ground/hover anchor, not each pose's bounding box.
            anchor=round(height*304/320)
            if state=='idle' and e[5]!='bat': anchor=bounds.bottom
        if e[5]=='boss' and prefix!='boss_ring':
            anchor=round(height*self.boss_source_anchors.get(frame_key,bounds.bottom/height))
        rect.x=sx-(width//2 if '_locomotion_' in frame_key or '_cast3_' in frame_key else bounds.centerx); rect.y=round(feet)-anchor
        return image,rect
