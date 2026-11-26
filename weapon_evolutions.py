"""Boss-exclusive, one-time weapon evolutions and their combat events.

Timers advance only with active simulation dt, so reward/pause screens cannot
silently expire a storm, a sword wave or a delayed afterimage.
"""
import math
import random
from rogue_content import WEAPONS

BOSS_EVOLUTION_CHANCE = .12
EVOLUTIONS = (
    ('evo_smg', '雷链蜂群', '命中向附近3敌连锁电击，每跳造成75%伤害', 3, 1),
    ('evo_shotgun', '震爆龙息', '每枪命中引爆2.8米冲击波，额外造成300%单弹伤害', 3, 1),
    ('evo_mg', '熔炉弹幕', '连续每8枪追加三枚穿透等离子弹，停火或切枪清热', 3, 1),
    ('evo_sniper', '星轨裂解', '子弹贯穿所有命中敌人，首个目标引发2.1米裂解爆炸', 3, 1),
    ('evo_sword', '破空剑潮', '每次挥砍追加10米穿透剑气，造成90%伤害', 3, 1),
    ('evo_boomerang', '三相回旋', '投出三把回旋刃，两侧副刃各造成70%伤害', 3, 1),
    ('evo_spear', '雷狱之锚', '命中或最远点生成3秒雷域，每半秒造成45%伤害', 3, 1),
    ('evo_dagger', '虚空重奏', '闪现后残影再斩90%伤害；残影击杀返精力并重置冷却', 3, 1),
)
EVOLUTIONS = tuple((key,f'{WEAPONS[i]["name"]}·质变强化：{title}',description,rank,scale)
                   for i,(key,title,description,rank,scale) in enumerate(EVOLUTIONS))
EVOLUTION_BY_KEY = {card[0]: i for i, card in enumerate(EVOLUTIONS)}
COLORS = ((75,220,255),(255,140,50),(255,210,75),(195,125,255),
          (80,255,215),(145,255,115),(85,175,255),(205,140,255))


class WeaponEvolutions:
    def __init__(self, game):
        self.g = game
        self.owned = set()
        self.clear()

    def clear(self):
        """Clear transient events between waves, but retain earned evolutions."""
        self.clock = 0.
        self.fx = []
        self.waves = []
        self.fields = []
        self.echoes = []
        self.reset_heat()

    def reset_heat(self):
        self.heat = 0
        self.last_mg = -10000

    def has(self, weapon):
        return weapon in self.owned

    def offer(self, boss):
        eligible = sorted((set(self.g.weapon_slots) & self.g.unlocked_weapons) - self.owned)
        if not boss or not eligible or random.random() >= BOSS_EVOLUTION_CHANCE:
            return None
        # Weight toward weapons the player actually uses without excluding the others.
        weights = [1 + self.g.weapon_usage[i] / max(1, sum(self.g.weapon_usage)) * 6 for i in eligible]
        return EVOLUTIONS[random.choices(eligible, weights=weights)[0]]

    def acquire(self, key):
        weapon = EVOLUTION_BY_KEY.get(key)
        if (weapon is None or weapon in self.owned or weapon not in self.g.unlocked_weapons
                or weapon not in self.g.weapon_slots):
            return False
        self.owned.add(weapon)
        return True

    def los(self, a, b):
        return self.g.world_los(*a[:2], *b[:2])

    def damage(self, enemy, amount, now, melee=False):
        if melee and enemy[5] == 'bat' and self.g.z < .5:
            return 0
        return self.g.damage_enemy(enemy, amount, now, method='melee' if melee else 'normal')

    def segment_fx(self, a, b, weapon, duration=.22):
        self.fx.append(dict(kind='line', a=tuple(a[:2]), b=tuple(b[:2]),
                            weapon=weapon, end=self.clock+duration))
        self.fx = self.fx[-80:]

    def burst(self, center, radius, damage, weapon, now, melee=False):
        center = tuple(center[:2])
        self.fx.append(dict(kind='ring', a=center, radius=radius, weapon=weapon, end=self.clock+.4))
        for enemy in list(self.g.enemies):
            if enemy[2] > 0 and math.dist(center, enemy[:2]) <= radius and self.los(center, enemy):
                self.damage(enemy, damage, now, melee)

    def gun_shot(self, weapon, targets, damage, now):
        if not self.has(weapon):
            return
        unique = []
        seen = set()
        for _, enemy, _ in targets:
            if id(enemy) not in seen:
                unique.append(enemy); seen.add(id(enemy))
        if weapon == 0 and unique:
            current = unique[0]
            visited = {id(current)}
            for _ in range(3):
                candidates = [e for e in self.g.enemies if e[2] > 0 and id(e) not in visited
                              and math.dist(current[:2], e[:2]) <= 3.5 and self.los(current, e)]
                if not candidates:
                    break
                target = min(candidates, key=lambda e: math.dist(current[:2], e[:2]))
                self.damage(target, damage*.75, now)
                self.segment_fx(current, target, 0)
                visited.add(id(target)); current = target
        elif weapon == 1 and unique:
            self.burst(unique[0], 2.8, damage*3, 1, now)
        elif weapon == 2:
            if self.clock-self.last_mg > .4:
                self.heat = 0
            self.last_mg = self.clock
            self.heat += 1
            if self.heat >= 8:
                self.heat = 0
                for offset in (-.16, 0, .16):
                    self.launch_wave(self.g.player, self.g.angle+offset, damage*1.3, 2, 20, .38)
        elif weapon == 3:
            origin = self.g.player
            endpoint = (origin[0]+math.cos(self.g.angle)*50, origin[1]+math.sin(self.g.angle)*50)
            # Clip the bright trace at cover, just like the actual hitscan.
            if not self.los(origin, endpoint):
                low,high = 0.,50.
                for _ in range(10):
                    mid = (low+high)/2
                    point = (origin[0]+math.cos(self.g.angle)*mid,origin[1]+math.sin(self.g.angle)*mid)
                    if self.los(origin,point): low=mid
                    else: high=mid
                endpoint = (origin[0]+math.cos(self.g.angle)*low,origin[1]+math.sin(self.g.angle)*low)
            self.segment_fx(origin, endpoint, 3, .35)
            if unique:
                self.burst(unique[0], 2.1, damage*.8, 3, now)

    def launch_wave(self, origin, angle, damage, weapon, reach=10, width=.7):
        self.waves.append(dict(pos=tuple(origin), angle=angle, damage=damage,
                               weapon=weapon, remaining=reach, width=width, hits=set()))

    def sword(self, now):
        if self.has(4):
            self.launch_wave(self.g.player, self.g.angle, self.g.damage*.9, 4)

    def spear_anchor(self, shot, position=None):
        if not self.has(6) or shot.get('evo_anchor'):
            return
        shot['evo_anchor'] = True
        self.fields.append(dict(pos=tuple(position) if position else (shot['x'],shot['y']), damage=shot['damage']*.45,
                                end=self.clock+3, next=self.clock))
        self.fields = self.fields[-2:]

    def dagger(self, path, damage):
        if self.has(7):
            self.echoes.append(dict(path=list(path), damage=damage*.9, at=self.clock+.3))
            self.segment_fx(path[0], path[-1], 7, .65)

    @staticmethod
    def segment_distance(point, a, b):
        dx,dy = b[0]-a[0],b[1]-a[1]
        t = max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/max(1e-9,dx*dx+dy*dy)))
        return math.dist(point[:2],(a[0]+t*dx,a[1]+t*dy))

    def update(self, dt, now):
        self.clock += dt
        self.fx = [f for f in self.fx if f['end'] > self.clock]
        if self.clock-self.last_mg > .4:
            self.heat = 0
        waves = []
        for wave in self.waves:
            start = wave['pos']; travel = min(wave['remaining'],dt*16)
            # Substep so a wave cannot hit an enemy past a wall after a lag spike.
            for step in range(max(1,math.ceil(travel/.12))):
                length = min(.12,travel-step*.12)
                a = wave['pos']
                b = (a[0]+math.cos(wave['angle'])*length,a[1]+math.sin(wave['angle'])*length)
                if not self.los(a,b):
                    wave['remaining'] = 0; break
                for enemy in self.g.enemies:
                    if enemy[2] > 0 and id(enemy) not in wave['hits'] and self.segment_distance(enemy,a,b) <= wave['width'] and self.los(b,enemy):
                        self.damage(enemy,wave['damage'],now,wave['weapon']==4)
                        wave['hits'].add(id(enemy))
                wave['pos'] = b
            wave['remaining'] -= travel
            self.segment_fx(start,wave['pos'],wave['weapon'],.12)
            if wave['remaining'] > 0:
                waves.append(wave)
        self.waves = waves
        for field in self.fields:
            if self.clock < field['end'] and self.clock >= field['next']:
                self.burst(field['pos'],2.4,field['damage'],6,now,True)
                field['next'] = self.clock+.5  # Never unload missed ticks after a stall.
        self.fields = [f for f in self.fields if f['end'] > self.clock]
        for echo in self.echoes:
            if self.clock < echo['at']:
                continue
            killed = False
            for enemy in self.g.enemies:
                if enemy[2] > 0 and any(math.dist(p,enemy[:2]) <= .85 and self.los(p,enemy) for p in echo['path']):
                    self.damage(enemy,echo['damage'],now,True)
                    killed |= enemy[2] <= 0
            if killed:
                self.g.stamina = min(self.g.max_stamina,self.g.stamina+14)
                if self.g.weapon_index == 7:
                    self.g.combat.cooldown = now
        self.echoes = [e for e in self.echoes if e['at'] > self.clock]

    def draw(self, surface):
        import pygame
        def lightning(origin, radius, color):
            for i in range(4):
                angle=i*math.tau/4+self.clock*1.5
                x=origin[0]+math.cos(angle)*radius*.72
                y=origin[1]+math.sin(angle)*radius*.72
                if not self.los(origin,(x,y)):
                    continue
                points=[self.g.project(x,y,z) for z in (-.45,.05,.6)]
                if all(points):
                    points[1]=(points[1][0]+7,points[1][1])
                    pygame.draw.lines(surface,color,False,points,3)
        for field in self.fields:
            self.g.combat._draw_circle(surface,field['pos'],2.4,color=COLORS[6])
            lightning(field['pos'],2.4,COLORS[6])
        for echo in self.echoes:
            # Reuse the existing authored assassin art along the blink path.
            for p in echo['path'][::max(1,len(echo['path'])//3)]:
                point=self.g.project(*p,.05)
                if point:
                    distance=max(.6,math.dist(p,self.g.player))
                    size=min(240,max(28,int(320/distance)))
                    self.g.cloud_art.blit(surface,'fx_dash',(point[0]-size//2,point[1]-size//2,size,size))
        for fx in self.fx:
            color = COLORS[fx['weapon']]
            if fx['kind'] == 'ring':
                self.g.combat._draw_circle(surface,fx['a'],fx['radius'],color=color)
                if fx['weapon']==1:
                    lightning(fx['a'],fx['radius'],color)
                continue
            a,b = fx['a'],fx['b']
            # Clip lines to the near plane rather than dropping a whole beam.
            def depth(p):
                return (p[0]-self.g.player[0])*math.cos(self.g.angle)+(p[1]-self.g.player[1])*math.sin(self.g.angle)
            da,db = depth(a),depth(b)
            if max(da,db) < .14:
                continue
            if da < .14:
                t=(.14-da)/max(1e-8,db-da); a=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
            elif db < .14:
                t=(.14-db)/max(1e-8,da-db); b=(b[0]+(a[0]-b[0])*t,b[1]+(a[1]-b[1])*t)
            # Trails start at body height, avoiding a vertical mast at the
            # near plane when a projectile departs from the player's position.
            pa,pb = self.g.project(*a,0),self.g.project(*b,0)
            if fx['weapon']==3 and math.dist(fx['a'],self.g.player)<.3:
                pa=(int(surface.get_width()*.78),int(surface.get_height()*.8))
            if pa and pb:
                if fx['weapon'] == 0:
                    mid=((pa[0]+pb[0])//2+10,(pa[1]+pb[1])//2-12)
                    pygame.draw.lines(surface,color,False,[pa,mid,pb],5)
                else:
                    pygame.draw.line(surface,color,pa,pb,6)
                pygame.draw.line(surface,(235,255,255),pa,pb,2)
        for wave in self.waves:
            a=wave['angle']; x,y=wave['pos']; w=wave['width']
            if wave['weapon']==4:
                points=[self.g.project(x-math.sin(a)*s-math.cos(a)*abs(s)*.5,
                                       y+math.cos(a)*s-math.sin(a)*abs(s)*.5,.15)
                        for s in (-w,-w*.5,0,w*.5,w)]
                if all(points):
                    pygame.draw.lines(surface,COLORS[4],False,points,9)
                    pygame.draw.lines(surface,(235,255,250),False,points,3)
            else:
                point=self.g.project(x,y,.15)
                if point:
                    radius=max(4,min(40,int(55/max(.5,math.dist((x,y),self.g.player)))))
                    pygame.draw.circle(surface,COLORS[2],point,radius)
                    pygame.draw.circle(surface,(255,255,215),point,max(2,radius//2))
        if self.has(self.g.weapon_index):
            title = EVOLUTIONS[self.g.weapon_index][1].split('：',1)[-1]
            if self.g.weapon_index == 2:
                title += f' · 热量 {self.heat}/8'
            image=self.g.card_font.render('质变 · '+title,True,(255,215,105))
            surface.blit(image,(surface.get_width()-image.get_width()-18,180))
