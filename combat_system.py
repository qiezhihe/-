"""Optional combat layer for melee weapons and boss patterns.

The class is deliberately decoupled from the renderer: pass the existing Game
instance and call attack/update from its input/update loops.  It is safe to use
without this module (all methods simply return False when unavailable).
"""
import math, random
try:
    from rogue_content import WEAPONS, BOSS_DESIGNS, BOSS_TELEGRAPH
except Exception:
    WEAPONS = []

class CombatSystem:
    SLAM_RADIUS=1.65
    HUNT_RADIUS=1.7
    DUEL_RADIUS=3.3
    CHARGE_RADIUS=1.35
    LASER_HALF_WIDTH=.45
    SNIPE_HALF_WIDTH=.35
    LASER_LENGTH=18
    LASER_AREA_RADIUS=1.35
    WINDUP_COMMON=900
    WINDUP_SIGNATURE=1200
    WINDUP_ENRAGED=800

    @staticmethod
    def laser_state(pattern, now):
        """Analytic forward / pause / reverse motion, shared by hits and visuals."""
        if not pattern.get('array'):
            elapsed=max(0,min(1,(now-pattern['windup'])/1600))
            return pattern['angle']+elapsed*math.pi*1.5,1,False
        duration=pattern['impact']-pattern['windup']
        pause=1000
        turn=(duration-pause)/2
        elapsed=max(0,min(duration,now-pattern['windup']))
        travel=min(elapsed,turn)-max(0,elapsed-turn-pause)
        speed=pattern.get('rotation_speed',.14)
        angle=pattern['angle']+travel/1000*speed
        direction=1 if elapsed<turn else 0 if elapsed<turn+pause else -1
        warning=now>=pattern['windup'] and turn-900<=elapsed<turn+pause
        return angle,direction,warning

    def laser_rays(self, pattern, now):
        angle,_,_=self.laser_state(pattern,now)
        count=pattern.get('beam_count',1)
        return [angle+i*math.tau/count for i in range(count)]

    def _update_laser(self, enemy, pattern, now):
        if now>=pattern['impact']: return
        origin=pattern['origin']; p=self.g.player
        width=pattern.get('beam_half_width',self.LASER_HALF_WIDTH)
        dx,dy=p[0]-origin[0],p[1]-origin[1]
        # At the edge of the arena even the enraged beam travels at <3 m/s;
        # unupgraded walking speed is 3.2 m/s. No mandatory jumping or sprint.
        if now>=pattern.get('damage_at',0) and abs(self.g.z)<.26 and self._los(origin,p):
            for angle in self.laser_rays(pattern,now):
                along=dx*math.cos(angle)+dy*math.sin(angle)
                across=abs(-dx*math.sin(angle)+dy*math.cos(angle))
                if 0<along<self.LASER_LENGTH and across<width:
                    self.g.hurt(12,source=origin);pattern['damage_at']=now+650
                    break  # Crossing beams cannot stack damage in one tick.
        if not pattern.get('array'):return
        zones=pattern.setdefault('zones',[])
        zones[:]=[zone for zone in zones if now<zone['end']]
        if now>=pattern.get('next_throw',pattern['windup']+600) and now+2350<pattern['impact']:
            # Snapshot, never a homing marker. Spawn from NOW after a lag spike,
            # not from an expired scheduled time, preserving the full warning.
            zones.append(dict(target=tuple(p),start=now,land=now+1250,end=now+2350,hit=False))
            pattern['next_throw']=now+1800
        for zone in zones:
            if now>=zone['land'] and not zone['hit']:
                zone['hit']=True
                if math.dist(p,zone['target'])<self.LASER_AREA_RADIUS and self.g.z<.4 and self._los(zone['target'],p):
                    self.g.hurt(14,source=zone['target'])

    def laser_status(self, pattern, now):
        if now<pattern['windup']:return '激光阵列蓄力 · 离开光带，保持移动'
        _,direction,warning=self.laser_state(pattern,now)
        if warning:return '激光即将反转 · 停顿后反向扫射'
        return ('顺时针' if direction>0 else '逆时针')+'缓扫 · 绕行光束，离开落点圈'

    @staticmethod
    def hammer_radius(stage):
        return 2.6+stage*.45

    def __init__(self, game):
        self.g = game; self.active=[]; self.cooldown=0; self.guard=False
        self.dash_until=0; self.boss_pattern={}; self.throws=[]; self.boss_cycles={}; self.boss_impacts=[]

    def _weapon(self):
        i=getattr(self.g,'weapon_index',0)
        return WEAPONS[i] if 0<=i<len(WEAPONS) else {}
    def _enemies(self): return getattr(self.g,'enemies',[])
    def _hit(self,e,dmg,now):
        if e[5]=='bat' and self.g.z<.5: return
        self.g.damage_enemy(e,dmg,now,method="melee"); self.g.hit_until=now+120
        self.g.sound('melee_hit')
        if now>=self.g.melee_heal_ready and self.g.extras.get('melee_sustain',0):
            self.g.hp=min(self.g.max_hp,self.g.hp+min(8,self.g.extras['melee_sustain']))
            self.g.melee_heal_ready=now+400
        duration=min(1.5,self.g.extras.get('melee_stagger',0))
        if duration: self.g.melee_staggers[id(e)]=now+duration*1000
    def _los(self,a,b):
        fn=getattr(self.g,'world_los',None)
        return fn(a[0],a[1],b[0],b[1]) if fn else True
    def _boss_projectile(self,enemy,angle,now,speed=None,vz=0):
        kind=('colossus','hunter','judge','weaver','executioner')[(self.g.wave//5-1)%5]
        velocity={'colossus':3.4,'hunter':7.,'judge':9.,'weaver':2.8,'executioner':5.5}[kind]
        damage={'colossus':18,'hunter':11,'judge':20,'weaver':12,'executioner':15}[kind]
        self.g.projectiles.append([enemy[0],enemy[1],math.cos(angle)*velocity,math.sin(angle)*velocity,
            damage+min(10,self.g.wave//5),now+6500,0,vz,'boss_'+kind])
    def attack(self, now, button=1):
        """Process non-gun attack. button=1 slash/throw, 3 defend."""
        w=self._weapon(); kind=w.get('kind');
        if kind not in ('melee','shield'): return False
        if button==3 and kind in ('shield','melee'):
            if getattr(self.g,'weapon_index',0)!=4: return False
            self.guard=True; setattr(self.g,'guarding',True); return True
        if button!=1 or now<self.cooldown: return True
        p=getattr(self.g,'player',[0,0]); ang=getattr(self.g,'angle',0); idx=getattr(self.g,'weapon_index',4)
        # One physical boomerang: holding attack must not spawn another before catch.
        if idx in (5,6) and any(s['kind']==('boomerang' if idx==5 else 'spear') for s in self.throws): return True
        if idx==7 and not self.g.spend_stamina(self.g.blink_stamina_cost,now):
            self.g.message='精力不足，无法闪现'; return True
        self.cooldown=now+max(120,getattr(self.g,'fire_delay',w.get('delay',420)))
        self.g.weapon_action_start=now
        self.g.sound(('sword_swing','boomerang_throw','spear_throw','dagger_dash')[idx-4])
        if idx==4: # sword: broad arc
            arc=min(math.pi*1.5,w.get('arc',1.8)*(1+self.g.extras.get('sword_arc',0)))
            for e in self._enemies():
                d=math.hypot(e[0]-p[0],e[1]-p[1]); rel=abs((math.atan2(e[1]-p[1],e[0]-p[0])-ang+math.pi)%(2*math.pi)-math.pi)
                if d<=w.get('range',2.2)*(1+min(1,self.g.extras.get('melee_reach',0))) and rel<=arc/2 and self._los(p,e): self._hit(e,self.g.damage,now)
            self.g.evolutions.sword(now)
            self.active.append(('slash',now+180,ang)); return True
        if idx==5: # returning boomerang
            for offset in ((-.38,0,.38) if self.g.evolutions.has(5) else (0,)):
                self.throws.append(dict(kind='boomerang',start=now,x=p[0],y=p[1],ox=p[0],oy=p[1],angle=ang+offset,damage=self.g.damage*(.7 if offset else 1),return_bonus=self.g.extras.get('boomerang_return',0),hits=set()))
            return True
        if idx==6: # penetrating spear
            self.throws.append(dict(kind='spear',start=now,x=p[0],y=p[1],ox=p[0],oy=p[1],angle=ang,damage=self.g.damage*(1+self.g.extras.get('spear_pierce',0)),hits=set())); return True
        if idx==7: # blink and strike
            start=tuple(p); path=[start]
            bonus=self.g.extras.get('dagger_dash',0)
            dist=w['range']*(1+bonus); steps=max(1,math.ceil(dist/.08))
            for _ in range(steps):
                self.g.move(math.cos(ang)*dist/steps,math.sin(ang)*dist/steps)
                path.append(tuple(self.g.player))
            for e in self._enemies():
                if any(math.hypot(e[0]-x,e[1]-y)<=.55 and self._los((x,y),e) for x,y in path):
                    self._hit(e,self.g.damage*(1+bonus),now)
            self.g.evolutions.dagger(path,self.g.damage*(1+bonus))
            self.active.append(('dash',now+160,ang)); return True
        return True
    def update(self, dt, now):
        p=getattr(self.g,'player',[0,0]); out=[]
        for a in self.active:
            typ,expiry,ang,*data=a
            if now>=expiry: continue
            if typ in ('boomerang','spear'):
                ox,oy,t=data; t+=dt*(8 if typ=='spear' else 7); x=p[0]+math.cos(ang)*t if typ=='boomerang' and t<3 else (data[0]+math.cos(ang)*t); y=p[1]+math.sin(ang)*t if typ=='boomerang' and t<3 else (data[1]+math.sin(ang)*t)
                if typ=='boomerang' and t>=3: x=p[0]; y=p[1]
                for e in self._enemies():
                    if math.hypot(e[0]-x,e[1]-y)<.45: self._hit(e, self._weapon().get('damage',35),now)
                out.append((typ,expiry,ang,ox,oy,t))
            else: out.append(a)
        self.active=out
        throws=[]
        for shot in self.throws:
            age=(now-shot['start'])/1000
            reach_bonus=1+min(1,self.g.extras.get('melee_reach',0))
            if shot['kind']=='boomerang' and age>=1.2: continue
            a=shot['angle']; old=(shot['x'],shot['y'])
            if shot['kind']=='boomerang':
                t=min(1,age/1.2); reach=WEAPONS[5]['range']*reach_bonus*math.sin(math.pi*t); curve=2*math.sin(2*math.pi*t)
                x=shot['ox']*(1-t)+p[0]*t+math.cos(a)*reach-math.sin(a)*curve
                y=shot['oy']*(1-t)+p[1]*t+math.sin(a)*reach+math.cos(a)*curve
            else:
                if age>3: continue
                limit=WEAPONS[6]['range']*reach_bonus
                if not shot.get('returning') and math.hypot(old[0]-shot['ox'],old[1]-shot['oy'])>=limit-.001:
                    self.g.evolutions.spear_anchor(shot)
                    shot['returning']=True
                if shot.get('returning'):
                    distance=math.hypot(p[0]-old[0],p[1]-old[1])
                    if distance<=max(.25,dt*18):
                        # Finish exactly once: the projectile is caught and
                        # removed, so holding attack cannot duplicate it.
                        shot['caught']=True
                        self.g.sound('spear_catch')
                        continue
                    x=old[0]+(p[0]-old[0])/distance*dt*18
                    y=old[1]+(p[1]-old[1])/distance*dt*18
                else:
                    step=min(dt*12,max(0,limit-math.hypot(old[0]-shot['ox'],old[1]-shot['oy'])))
                    x=old[0]+math.cos(a)*step; y=old[1]+math.sin(a)*step
            if not self._los(old,(x,y)):
                if shot['kind']=='spear' and not shot.get('returning'):
                    self.g.evolutions.spear_anchor(shot)
                    shot['returning']=True; throws.append(shot)
                    continue
                if shot['kind']=='spear' and shot.get('returning'):
                    # Recall may pass through cover, but it remains a damaging
                    # sweep on the way back to the player.
                    pass
                else:
                    continue
            vx=x-old[0]; vy=y-old[1]
            for e in self._enemies():
                t=max(0,min(1,((e[0]-old[0])*vx+(e[1]-old[1])*vy)/max(1e-8,vx*vx+vy*vy)))
                pass_id=(id(e),age>.6) if shot['kind']=='boomerang' else id(e)
                contact=(old[0]+vx*t,old[1]+vy*t)
                if pass_id not in shot['hits'] and math.hypot(e[0]-contact[0],e[1]-contact[1])<.4 and (shot.get('returning') or self._los(contact,e)):
                    bonus=shot.get('return_bonus',0) if shot['kind']=='boomerang' and age>.6 else 0
                    self._hit(e,shot['damage']*(1+bonus),now); shot['hits'].add(pass_id)
                    if shot['kind']=='spear': self.g.evolutions.spear_anchor(shot,contact)
            shot.setdefault('trail',[]).append(old)
            shot['trail']=shot['trail'][-10:]
            shot['x']=x; shot['y']=y; throws.append(shot)
        self.throws=throws
        self.boss_impacts=[effect for effect in self.boss_impacts if effect[3]>now]
        living={id(e) for e in self._enemies() if e[2]>0}
        self.boss_pattern={key:value for key,value in self.boss_pattern.items() if key in living}
        self.boss_cycles={key:value for key,value in self.boss_cycles.items() if key in living}
        for enemy in self._enemies():
            if enemy[2]<=0: continue
            dash=self.boss_pattern.get(id(enemy))
            if isinstance(dash,dict):
                if now>=dash['recover']:
                    self.boss_pattern.pop(id(enemy),None)
                    continue
                if now<dash['windup']: continue
                if dash.get('skill') in ('hammer','hunt','snipe','brood','duel'):
                    self._update_signature(enemy,dash,now)
                    continue
                if dash.get('skill')=='slam':
                    if now>=dash['impact'] and not dash['hit']:
                        dash['hit']=True
                        self.boss_impacts.append((*dash['target'],'slam',now+650,self.SLAM_RADIUS))
                        if math.hypot(p[0]-dash['target'][0],p[1]-dash['target'][1])<self.SLAM_RADIUS and self.g.z<.4 and self._los(enemy,p): self.g.hurt(22,source=dash['target'])
                    if now>=dash['recover']: self.boss_pattern.pop(id(enemy),None)
                    continue
                if dash.get('skill')=='laser':
                    self._update_laser(enemy,dash,now)
                    if now>=dash['recover']: self.boss_pattern.pop(id(enemy),None)
                    continue
                if dash.get('skill')=='split':
                    if not dash['hit']:
                        dash['hit']=True
                        # Visible projectile clusters originate at three separated emitters.
                        for side in (-1,0,1):
                            ox=enemy[0]-math.sin(dash['angle'])*side*.8
                            oy=enemy[1]+math.cos(dash['angle'])*side*.8
                            for offset in (-.18,0,.18):
                                angle=dash['angle']+offset+side*.22
                                self._boss_projectile((ox,oy),angle,now)
                    if now>=dash['recover']: self.boss_pattern.pop(id(enemy),None)
                    continue
                if dash.get('skill')!='charge':
                    if not dash['hit']:
                        dash['hit']=True
                        for offset in dash['spreads']:
                            angle=dash['angle']+offset
                            self._boss_projectile(enemy,angle,now,vz=dash['vz'])
                    if now>=dash['recover']: self.boss_pattern.pop(id(enemy),None)
                    continue
                if not dash['hit']:
                    fraction=min(1,(now-dash['windup'])/(dash['impact']-dash['windup']))
                    nx=dash['origin'][0]+(dash['target'][0]-dash['origin'][0])*fraction
                    ny=dash['origin'][1]+(dash['target'][1]-dash['origin'][1])*fraction
                    # Substeps and body clearance stop a charge clipping corners.
                    steps=max(1,math.ceil(math.hypot(nx-enemy[0],ny-enemy[1])/.08))
                    ox,oy=enemy[:2]
                    for step in range(1,steps+1):
                        x=ox+(nx-ox)*step/steps; y=oy+(ny-oy)*step/steps
                        if not self.g.enemy_position_clear(x,y): break
                        enemy[0],enemy[1]=x,y
                if now>=dash['impact'] and not dash['hit']:
                    dash['hit']=True
                    self.boss_impacts.append((*enemy[:2],'hunter_charge',now+450,self.CHARGE_RADIUS))
                    if math.hypot(p[0]-enemy[0],p[1]-enemy[1])<self.CHARGE_RADIUS and self._los(enemy,p): self.g.hurt(18,source=enemy[:2])
                if now>=dash['recover']: self.boss_pattern.pop(id(enemy),None)
                continue
            if dash and now<dash[0]:
                _,angle=dash
                nx=enemy[0]+math.cos(angle)*dt*7; ny=enemy[1]+math.sin(angle)*dt*7
                if self._los(enemy,(nx,ny)):
                    enemy[0]=nx; enemy[1]=ny
                if math.hypot(enemy[0]-p[0],enemy[1]-p[1])<.65:
                    self.g.hurt(18,source=enemy[:2]); self.boss_pattern.pop(id(enemy),None)
    def boss_attack(self, enemy, now):
        if enemy is None or enemy[2]<=0: return False
        if id(enemy) in self.boss_pattern: return False
        p=getattr(self.g,'player',[0,0]); ang=math.atan2(p[1]-enemy[1],p[0]-enemy[0]); typ=(getattr(self.g,'wave',1)//5-1)%5
        cycle=self.boss_cycles.get(id(enemy),0); self.boss_cycles[id(enemy)]=cycle+1
        skills=BOSS_DESIGNS[typ]['skills']
        phase=cycle%len(skills);preferred=skills[phase]
        telegraph=BOSS_TELEGRAPH[typ] if typ<len(BOSS_TELEGRAPH) and BOSS_TELEGRAPH[typ].get('enabled') else None
        # Each encounter has a signature attack, rather than only rearranging
        # the same projectile patterns. Low health changes the signature rhythm.
        if preferred in ('hammer','hunt','snipe','brood','duel'):
            skill=preferred
            enraged=enemy[2]<=enemy[4]*.5
            delay=(1500,1250,1700,1900,1450)[typ]
            if telegraph: delay=self.WINDUP_ENRAGED if enraged else self.WINDUP_SIGNATURE
            self.g.sound('boss_'+skill if telegraph else 'boss_charge')
            self.boss_pattern[id(enemy)]=dict(skill=skill,origin=tuple(enemy[:2]),target=tuple(p),angle=ang,
                windup=now+delay,impact=now+delay+1800,recover=now+delay+2900,
                hit=False,stage=0,enraged=enraged,telegraph=telegraph)
            if telegraph: self._boss_cue(telegraph['signature_cue'],now)
            else:
                self.g.message=('巨像：三连地锤 · 跳过震荡，末击后反击','猎王：锁点突扑 · 横移避开猎杀路径',
                    '审判官：贯穿狙击 · 躲入掩体','织母：孵化仪式 · 清理护卫，留意本体',
                    '执刑者：延迟剑舞 · 躲开末段再反击')[typ]
            return True
        if preferred=='slam':
            windup=now+(self.WINDUP_ENRAGED if enemy[2]<=enemy[4]*.5 else self.WINDUP_COMMON) if telegraph else now+1000
            if telegraph: self.g.sound('boss_'+telegraph['cue'])
            self.boss_pattern[id(enemy)]=dict(skill='slam',origin=tuple(enemy[:2]),target=tuple(p),windup=windup,impact=windup+700,recover=windup+1800,hit=False,telegraph=telegraph)
            if telegraph: self.g.boss_cue_text=''
            else: self.g.message='BOSS：跃空震击 · 离开落点，落地后反击'
            return True
        if preferred=='laser':
            enraged=enemy[2]<=enemy[4]*.5
            if typ!=2:
                # The long reversing barrage belongs only to the third Boss.
                self.boss_pattern[id(enemy)]=dict(skill='laser',origin=tuple(enemy[:2]),target=tuple(p),angle=ang,
                    windup=now+1100,impact=now+2700,recover=now+3500,hit=False)
                self.g.message='BOSS：旋转射线 · 蓄力后逆向绕行'
                return True
            windup=now+1500;duration=11000 if enraged else 9000
            self.boss_pattern[id(enemy)]=dict(skill='laser',origin=tuple(enemy[:2]),target=tuple(p),angle=ang,
                windup=windup,impact=windup+duration,recover=windup+duration+1500,hit=False,
                beam_count=4 if enraged else 3,beam_half_width=.7 if enraged else .6,
                rotation_speed=.16 if enraged else .14,enraged=enraged,array=True,zones=[],next_throw=windup+600)
            self.g.message='审判激光阵列：多束缓扫 · 留意反转与投掷落点'
            return True
        if preferred=='split':
            self.boss_pattern[id(enemy)]=dict(skill='split',target=tuple(p),angle=ang,windup=now+950,impact=now+1050,recover=now+1900,hit=False)
            self.g.message='BOSS：分裂齐射 · 避开三组发射口'
            return True
        if preferred=='charge':
            self.boss_pattern[id(enemy)]=dict(skill='charge',origin=tuple(enemy[:2]),target=tuple(p),windup=now+900,impact=now+1450,recover=now+2350,hit=False)
            self.g.message='BOSS：定点冲撞 · 离开橙色范围'
            return True
        patterns=(
            (('酸液扇射',(-.55,-.28,0,.28,.55),5),('交叉散射',tuple(i*math.pi/2 for i in range(4)),4),('密集喷吐',(-.12,-.06,0,.06,.12),6)),
            (('冲撞',(),5),('肩炮齐射',(-.22,0,.22),6),('震荡弹环',tuple(i*math.tau/10 for i in range(10)),3.5)),
            (('维度弹环',tuple(i*math.tau/12 for i in range(12)),4),('裂隙扇射',(-.7,-.35,0,.35,.7),5),('旋角弹环',tuple(i*math.tau/8+math.pi/8 for i in range(8)),5)))
        if preferred=='ring': name,spreads,speed=('震荡弹环',tuple(i*math.tau/10 for i in range(10)),3.5)
        elif preferred=='fan': name,spreads,speed=('扇形爆裂',(-.55,-.28,0,.28,.55),5)
        else: name,spreads,speed=patterns[typ%3][phase]
        if typ==0: spreads=(-.45,0,.45)  # Three weighty rocks, not a dense light curtain.
        elif typ==1: spreads=(-.18,0,.18)
        elif typ==2: spreads=(0,)
        elif typ==3: spreads=(-.65,-.32,0,.32,.65)
        distance=max(.5,math.hypot(p[0]-enemy[0],p[1]-enemy[1]))
        windup=now+(self.WINDUP_ENRAGED if enemy[2]<=enemy[4]*.5 else self.WINDUP_COMMON) if telegraph else now+750
        if telegraph: self.g.sound('boss_'+telegraph['cue'])
        self.boss_pattern[id(enemy)]=dict(skill=name,target=tuple(p),angle=ang,spreads=spreads,speed=speed,vz=self.g.z*speed/distance,windup=windup,impact=windup+100,recover=windup+750,hit=False,telegraph=telegraph)
        if telegraph: self.g.boss_cue_text=''
        else: self.g.message='BOSS：'+name+' · 蓄力中，注意躲避'
        return True
    def _boss_cue(self,text,now,duration=2000):
        self.g.boss_cue_text=text; self.g.boss_cue_until=now+duration
    def _update_signature(self,enemy,pattern,now):
        """Timed signature attacks: finite emissions, capped damage and recovery."""
        if now>=pattern['impact']: return
        skill=pattern['skill']; elapsed=now-pattern['windup']; stage=pattern['stage']
        p=self.g.player; origin=pattern['origin']; target=pattern['target']
        count=4 if pattern['enraged'] else 3
        interval=450 if pattern['enraged'] else 600
        if skill=='brood':
            if not pattern['hit']:
                self.g.sound('boss_brood')
                pattern['hit']=True
                # Summons are ordinary enemies and participate in existing kills,
                # pathfinding and wave completion; never unlimited spawning.
                for dx,dy in ((-1,0),(1,0),(0,1))[:3 if pattern['enraged'] else 2]:
                    x,y=enemy[0]+dx,enemy[1]+dy
                    if self.g.enemy_position_clear(x,y) and len(self.g.enemies)<28:
                        hp=45+self.g.wave*5
                        self.g.enemies.append([x,y,hp,0,hp,'runner',now+1800])
                self.boss_impacts.append((*enemy[:2],'split',now+700))
            return
        if skill=='hunt':
            if not pattern['hit']:
                t=min(1,elapsed/550)
                self.g.move_enemy(enemy,origin[0]+(target[0]-origin[0])*t-enemy[0],origin[1]+(target[1]-origin[1])*t-enemy[1])
            if elapsed>=550 and not pattern['hit']:
                self.g.sound('boss_hunt')
                pattern['hit']=True
                self.boss_impacts.append((*enemy[:2],'hunt',now+600,self.HUNT_RADIUS))
                if math.dist(p,enemy[:2])<self.HUNT_RADIUS and self._los(enemy,p): self.g.hurt(20,source=enemy[:2])
            return
        if stage>=count or elapsed<stage*interval: return
        pattern['stage']+=1
        self.g.sound('boss_'+skill)
        if skill=='hammer':
            radius=self.hammer_radius(stage)
            self.boss_impacts.append((*target,'slam',now+650,radius))
            if math.dist(p,target)<radius and self.g.z<.4 and self._los(enemy,p): self.g.hurt(14,source=target)
        elif skill=='snipe':
            # Locked bearing, cover and jumping are valid responses.
            a=pattern['angle']; dx=p[0]-origin[0]; dy=p[1]-origin[1]
            along=dx*math.cos(a)+dy*math.sin(a); across=abs(-dx*math.sin(a)+dy*math.cos(a))
            if 0<along<24 and across<self.SNIPE_HALF_WIDTH and abs(self.g.z)<.3 and self._los(enemy,p): self.g.hurt(16,source=origin)
        elif skill=='duel':
            self.boss_impacts.append((*enemy[:2],'rupture',now+500,self.DUEL_RADIUS))
            if math.dist(p,enemy[:2])<self.DUEL_RADIUS and self.g.z<.4 and self._los(enemy,p): self.g.hurt(15,source=enemy[:2])
            a=pattern['angle']+(stage-1)*.25
            self._boss_projectile(enemy,a,now)
    def _ground_polygon(self, vertices, elevation=-.495):
        """Clip in world space so a danger zone remains visible when inside it."""
        p=self.g.player; angle=self.g.angle
        def depth(v): return (v[0]-p[0])*math.cos(angle)+(v[1]-p[1])*math.sin(angle)
        clipped=[]
        for a,b in zip(vertices,vertices[1:]+vertices[:1]):
            da,db=depth(a),depth(b)
            if da>=.13: clipped.append(a)
            if (da>=.13)!=(db>=.13):
                t=(.13-da)/(db-da)
                clipped.append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
        return [self.g.project(*v,elevation) for v in clipped]

    def _draw_zone(self,surface,vertices,color,key=None,elevation=-.495,fill=True):
        import pygame
        points=self._ground_polygon(vertices,elevation)
        if len(points)<3 or any(p is None for p in points): return
        bounds=pygame.Rect(min(p[0] for p in points),min(p[1] for p in points),
                           max(p[0] for p in points)-min(p[0] for p in points)+1,
                           max(p[1] for p in points)-min(p[1] for p in points)+1)
        bounds=bounds.clip(surface.get_rect())
        if not bounds.width or not bounds.height: return
        local=[(x-bounds.x,y-bounds.y) for x,y in points]
        layer=pygame.Surface(bounds.size,pygame.SRCALPHA)
        if fill: pygame.draw.polygon(layer,(*color,65),local)
        art=getattr(self.g,'cloud_art',None)
        if key and art and key in art.images:
            texture=pygame.transform.scale(art.images[key],bounds.size)
            mask=pygame.Surface(bounds.size,pygame.SRCALPHA)
            pygame.draw.polygon(mask,(255,255,255,255),local)
            texture.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
            layer.blit(texture,(0,0))
        pygame.draw.polygon(layer,(*color,235),local,3)
        surface.blit(layer,bounds)

    def _draw_circle(self,surface,center,radius,key=None,color=(255,135,55)):
        vertices=[(center[0]+math.cos(i*math.tau/96)*radius,
                   center[1]+math.sin(i*math.tau/96)*radius) for i in range(96)]
        self._draw_zone(surface,vertices,color,key)

    def _draw_ring(self,surface,center,radius,color):
        vertices=[(center[0]+math.cos(i*math.tau/64)*radius,
                   center[1]+math.sin(i*math.tau/64)*radius) for i in range(64)]
        self._draw_zone(surface,vertices,color,fill=False)

    def _draw_rift(self,surface,center,radius,color):
        import pygame
        for i in range(8):
            a=i*math.tau/8+self.g.now*.0012
            inner=self.g.project(center[0]+math.cos(a)*radius*.28,center[1]+math.sin(a)*radius*.28,-.48)
            outer=self.g.project(center[0]+math.cos(a)*radius*.94,center[1]+math.sin(a)*radius*.94,-.48)
            if inner and outer: pygame.draw.line(surface,color,inner,outer,2)

    def _draw_corridor(self,surface,origin,angle,length,half_width,active=False,color=None):
        # LOS checks the whole prefix. Binary-search its first obstruction;
        # avoid hundreds of full ray walks per beam per rendered frame.
        end=length;endpoint=(origin[0]+math.cos(angle)*end,origin[1]+math.sin(angle)*end)
        if not self._los(origin,endpoint):
            low,high=0,length
            for _ in range(10):
                mid=(low+high)/2
                if self._los(origin,(origin[0]+math.cos(angle)*mid,origin[1]+math.sin(angle)*mid)):low=mid
                else:high=mid
            end=low
        vertices=[(origin[0]+math.cos(angle)*d-math.sin(angle)*side,
                   origin[1]+math.sin(angle)*d+math.cos(angle)*side)
                  for d,side in ((0,-half_width),(end,-half_width),(end,half_width),(0,half_width))]
        tint=color or ((255,65,125) if active else (205,115,135))
        self._draw_zone(surface,vertices,tint)
        if active:
            # A solid-looking low light wall, not just a faint floor triangle.
            self._draw_zone(surface,vertices,tint,elevation=0)
            for a,b in ((vertices[0],vertices[1]),(vertices[3],vertices[2])):
                bottom=self._ground_polygon([a,b],-.49)
                top=self._ground_polygon([b,a],.16)
                points=bottom+top
                if len(points)==4 and all(p is not None for p in points):
                    import pygame
                    layer=pygame.Surface(surface.get_size(),pygame.SRCALPHA)
                    pygame.draw.polygon(layer,(*tint,65),points)
                    pygame.draw.lines(layer,(*tint,230),False,top,3)
                    surface.blit(layer,(0,0))

    def _draw_laser_zones(self,surface,pattern):
        import pygame
        now=self.g.now;art=getattr(self.g,'cloud_art',None)
        for zone in pattern.get('zones',[]):
            if now>=zone['end']:continue
            landed=now>=zone['land'];target=zone['target']
            self._draw_circle(surface,target,self.LASER_AREA_RADIUS,color=(255,80,100) if landed else (255,190,75))
            if not landed:
                t=max(0,min(1,(now-zone['start'])/(zone['land']-zone['start'])))
                origin=pattern['origin']
                pos=(origin[0]+(target[0]-origin[0])*t,origin[1]+(target[1]-origin[1])*t)
                point=self.g.project(*pos,-.35+math.sin(t*math.pi)*2)
                if point:
                    pygame.draw.circle(surface,(255,230,145),point,7)
                    if art:art.blit(surface,'fx_boss_ammo_judge',(point[0]-18,point[1]-18,36,36))
                self._draw_circle(surface,target,self.LASER_AREA_RADIUS*(1-t),color=(255,225,155))
            else:
                phase=(now-zone['land'])/(zone['end']-zone['land'])
                self._draw_circle(surface,target,self.LASER_AREA_RADIUS*min(1,.3+phase*2),color=(255,90,125))

    def draw_status(self,surface):
        """HUD cue is separate from the world layer, so actors cannot hide it."""
        import pygame
        for pattern in self.boss_pattern.values():
            if not isinstance(pattern,dict) or not pattern.get('array') or self.g.now>=pattern['impact']:continue
            text=self.laser_status(pattern,self.g.now)
            _,_,warning=self.laser_state(pattern,self.g.now)
            label=self.g.font.render(text,True,(255,205,85) if warning else (255,160,190))
            rect=label.get_rect(midtop=(surface.get_width()//2,172))
            pygame.draw.rect(surface,(20,24,38),rect.inflate(18,8),border_radius=5)
            surface.blit(label,rect)

    def draw(self, surface):
        import pygame
        art=getattr(self.g,'cloud_art',None)
        if art:
            for effect in self.boss_impacts:
                x,y,key,expiry=effect[:4]
                if len(effect)>4:
                    if key in ('hunt','hunter_charge'):
                        self._draw_circle(surface,(x,y),effect[4],'fx_signature_hunt',(255,55,95))
                    else:self._draw_circle(surface,(x,y),effect[4],'fx_boss_'+key)
                    continue
                point=self.g.project(x,y,-.4)
                distance=max(.5,math.hypot(x-self.g.player[0],y-self.g.player[1]))
                size=min(480,max(48,int(650/distance)))
                if point: art.blit(surface,'fx_boss_'+key,(point[0]-size//2,point[1]-size//2,size,size))
        for enemy_id,pattern in self.boss_pattern.items():
            if art and isinstance(pattern,dict):
                enemy=next((e for e in self._enemies() if id(e)==enemy_id and e[2]>0),None)
                signature=pattern.get('skill')
                telegraph=pattern.get('telegraph')
                if enemy and signature in ('hammer','hunt','duel','slam','charge') and self.g.now<pattern['impact']:
                    center=enemy[:2] if signature=='duel' else pattern['target']
                    stage=min(pattern.get('stage',0),3 if pattern.get('enraged') else 2)
                    radius={'hammer':self.hammer_radius(stage),'hunt':self.HUNT_RADIUS,
                            'duel':self.DUEL_RADIUS,'slam':self.SLAM_RADIUS,'charge':self.CHARGE_RADIUS}[signature]
                    hunter=signature in ('hunt','charge')
                    tint=telegraph['color'] if telegraph and not hunter else (255,55,95) if hunter else (255,135,55)
                    self._draw_circle(surface,center,radius,color=tint)
                    if telegraph and signature=='hammer' and self.g.now<pattern['windup']:
                        self._draw_rift(surface,center,radius,telegraph['accent'])
                        last=3 if pattern.get('enraged') else 2
                        for future in range(stage+1,last+1):
                            self._draw_ring(surface,center,self.hammer_radius(future),telegraph['accent'])
                    if hunter:
                        origin=pattern['origin'];target=pattern['target']
                        angle=math.atan2(target[1]-origin[1],target[0]-origin[0])
                        distance=math.dist(origin,target)
                        self._draw_corridor(surface,origin,angle,distance,.22,color=(240,60,100))
                if enemy and telegraph and signature not in ('hammer','hunt','duel','slam','charge','laser','split','brood','snipe') and self.g.now<pattern.get('windup',0):
                    angle=pattern.get('angle',0.); spreads=pattern.get('spreads',(0,)); lo,hi=min(spreads),max(spreads)
                    arc=[(enemy[0]+math.cos(angle+lo+(hi-lo)*i/8)*8.,enemy[1]+math.sin(angle+lo+(hi-lo)*i/8)*8.) for i in range(9)]
                    self._draw_zone(surface,[enemy[:2]]+arc,telegraph['color'])
                if enemy and signature=='brood':
                    point=self.g.project(*enemy[:2],.35)
                    if point and pattern['windup']<=self.g.now<pattern['impact'] and (self.g.now-pattern['windup'])%600<250:
                        distance=max(1,math.dist(enemy[:2],self.g.player))
                        size=min(780,max(90,int(1300/distance)))
                        art.blit(surface,'fx_signature_'+signature,(point[0]-size//2,point[1]-size//2,size,size))
                if enemy and self.g.now<pattern['windup']:
                    point=self.g.project(enemy[0],enemy[1],.5)
                    cue='fx_signature_hunt' if (self.g.wave//5-1)%5==1 else 'fx_boss_charge'
                    if point: art.blit(surface,cue,(point[0]-60,point[1]-60,120,120))
                if enemy and signature=='hunt' and pattern['windup']<=self.g.now<pattern['windup']+650:
                    point=self.g.project(enemy[0],enemy[1],.25)
                    distance=max(1,math.dist(enemy[:2],self.g.player))
                    size=min(340,max(65,int(600/distance)))
                    if point:art.blit(surface,'fx_signature_hunt',(point[0]-size//2,point[1]-size//2,size,size))
                if enemy and pattern.get('skill')=='snipe' and self.g.now<pattern['impact']:
                    origin=pattern['origin']; angle=pattern['angle']
                    self._draw_corridor(surface,origin,angle,24,self.SNIPE_HALF_WIDTH,self.g.now>=pattern['windup'])
                if pattern.get('skill')=='brood' and self.g.now<pattern['impact']:
                    point=self.g.project(*pattern['target'],-.48)
                    distance=max(.5,math.hypot(pattern['target'][0]-self.g.player[0],pattern['target'][1]-self.g.player[1]))
                    size=min(400,max(24,int(500/distance)))
                    if point: art.blit(surface,'fx_boss_warning',(point[0]-size//2,point[1]-size//4,size,size//2))
            if isinstance(pattern,dict) and pattern.get('skill')=='laser':
                if self.g.now<pattern['impact']:
                    _,_,warning=self.laser_state(pattern,self.g.now)
                    for angle in self.laser_rays(pattern,self.g.now):
                        self._draw_corridor(surface,pattern['origin'],angle,self.LASER_LENGTH,
                            pattern.get('beam_half_width',self.LASER_HALF_WIDTH),self.g.now>=pattern['windup'],
                            color=(255,200,60) if warning else (255,65,125))
                    self._draw_laser_zones(surface,pattern)
            if art: continue
            if not isinstance(pattern,dict) or pattern.get('skill')!='charge' or self.g.now>=pattern['impact']: continue
            points=[self.g.project(pattern['target'][0]+math.cos(i*math.tau/32)*1.35,pattern['target'][1]+math.sin(i*math.tau/32)*1.35,-.48) for i in range(33)]
            if all(p is not None for p in points): pygame.draw.lines(surface,(255,110,55),False,points,3)
        for shot in self.throws:
            point=self.g.project(shot['x'],shot['y'],0)
            if point:
                x,y=point
                trail=[self.g.project(px,py,0) for px,py in shot.get('trail',[])]
                trail=[p for p in trail if p]
                color=(120,255,175) if shot['kind']=='boomerang' else (100,220,255)
                if len(trail)>1 and shot['kind']=='boomerang': pygame.draw.lines(surface,color,False,trail[-3:]+[point],1)
                art=getattr(self.g,'cloud_art',None)
                source=art.images.get('fx_'+shot['kind']) if art else None
                if source:
                    distance=max(.5,math.hypot(shot['x']-self.g.player[0],shot['y']-self.g.player[1]))
                    size=max(16,min(120,int(140/distance)))
                    frame=pygame.transform.scale(source,(size,size))
                    if shot['kind']=='boomerang':
                        angle=-int((self.g.now-shot['start'])*.9)//15*15
                    else:
                        ahead=self.g.project(shot['x']+math.cos(shot['angle'])*.25,shot['y']+math.sin(shot['angle'])*.25,0)
                        angle=math.degrees(math.atan2(-(ahead[1]-y),ahead[0]-x)) if ahead else 0
                    frame=pygame.transform.rotate(frame,angle)
                    surface.blit(frame,frame.get_rect(center=point))
                elif shot['kind']=='boomerang':
                    pygame.draw.lines(surface,(255,205,80),False,[(x-18,y-12),(x,y+9),(x+18,y-12)],6)
                else:
                    pygame.draw.line(surface,(160,240,255),(x-24,y+18),(x+24,y-18),5)
                    pygame.draw.polygon(surface,(240,255,255),[(x+24,y-18),(x+10,y-15),(x+20,y-3)])
        for a in self.active:
            w,h=surface.get_size()
            progress=1-max(0,(a[1]-self.g.now))/(180 if a[0]=='slash' else 160)
            if a[0]=='slash':
                # Screen-relative sweep, not world heading: it follows the hand animation.
                rect=pygame.Rect(int(w*.27),int(h*.27),int(w*.48),int(h*.5))
                start=.15+progress*1.4
                pygame.draw.arc(surface,(65,205,215),rect,start,start+1.25,9)
                pygame.draw.arc(surface,(215,255,245),rect.inflate(-8,-8),start,start+1.15,3)
            elif a[0]=='dash':
                for i in range(8):
                    angle=i*math.tau/8
                    outer=(int(w/2+math.cos(angle)*w*.48),int(h/2+math.sin(angle)*h*.46))
                    inner=(int(w/2+math.cos(angle)*w*.29),int(h/2+math.sin(angle)*h*.28))
                    pygame.draw.line(surface,(155,105,245),inner,outer,3)
    def draw_weapon(self, surface, center, gun_y):
        import pygame
        idx=self.g.weapon_index; x,y=center
        swing=max(0,(self.cooldown-self.g.now)/max(1,self.g.fire_delay))
        x+=int(math.sin(swing*math.pi)*65)
        if idx==4:
            if self.g.guarding: x-=75; y-=35
            pygame.draw.polygon(surface,(165,180,205),[(x-8,y+30),(x+9,y+27),(x+72,y-125),(x+55,y-145)])
            pygame.draw.line(surface,(245,250,255),(x+5,y+15),(x+59,y-127),3)
            pygame.draw.line(surface,(225,170,65),(x-27,y+32),(x+33,y+45),9)
            pygame.draw.line(surface,(80,48,36),(x,y+42),(x-15,y+110),15)
        elif idx==5:
            pygame.draw.lines(surface,(240,170,50),False,[(x-68,y-52),(x,y+12),(x+68,y-52)],18)
            pygame.draw.lines(surface,(250,240,200),False,[(x-68,y-60),(x,y+3),(x+68,y-60)],4)
        elif idx==6:
            pygame.draw.line(surface,(95,65,40),(x-65,y+130),(x+65,y-115),14)
            pygame.draw.polygon(surface,(170,230,240),[(x+65,y-160),(x+38,y-100),(x+78,y-89)])
        else:
            pygame.draw.polygon(surface,(185,115,250),[(x-12,y+45),(x+10,y+35),(x+35,y-70),(x+6,y-55)])
            pygame.draw.line(surface,(240,205,255),(x+10,y+35),(x+35,y-70),3)
            pygame.draw.line(surface,(55,40,70),(x-2,y+40),(x-18,y+105),15)
    def icon(self, surface, key, center):
        import pygame
        colors={'sword':(220,220,240),'boomerang':(240,170,60),'spear':(160,180,190),'dagger':(190,80,230)}
        x,y=center; col=colors.get(key,(180,180,180))
        if key=='boomerang': pygame.draw.lines(surface,col,False,[(x-22,y-12),(x,y+14),(x+22,y-12)],6)
        elif key=='spear':
            pygame.draw.line(surface,col,(x-18,y+20),(x+15,y-15),5)
            pygame.draw.polygon(surface,col,[(x+22,y-23),(x+5,y-17),(x+17,y-5)])
        else:
            pygame.draw.polygon(surface,col,[(x-6,y+14),(x+3,y+18),(x+17,y-24),(x+5,y-15)])
            pygame.draw.line(surface,(240,175,70),(x-14,y+12),(x+12,y+22),5)
