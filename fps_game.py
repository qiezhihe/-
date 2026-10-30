"""Minimal asset-free FPS prototype for PyCharm (pygame ray-caster).
Controls: WASD move, mouse aim, hold LMB fire, R reload, ESC pause, Q quit.
"""
import math
import random
from collections import deque
import os
from pathlib import Path
from array import array
import pygame
from rogue_content import UPGRADES as ALL_UPGRADES, WEAPONS, TIERS, SPECIALS, BALANCE
from combat_system import CombatSystem
from rogue_content import HYBRID_CARDS
from map_art import MapArt
from enemy_art import EnemyArt
from cloud_art import CloudArt


def load_font(size):
    """Load files directly: SysFont can fail on malformed Windows registry entries."""
    font_dir = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    candidates = [Path(__file__).resolve().parent / 'assets' / 'font.ttf']
    candidates += [font_dir / name for name in ('msyh.ttc', 'simhei.ttf', 'simsun.ttc', 'segoeui.ttf')]
    for path in candidates:
        try:
            if path.is_file():
                return pygame.font.Font(str(path), size)
        except (OSError, ValueError, TypeError, pygame.error):
            continue
    return pygame.font.Font(None, size)

W, H = 960, 600
VERSION = '0.2.0-rc1'
THEME = {
    # 原创成人科幻动画风格：酸液绿、传送门青、实验室紫蓝，不使用受版权保护角色素材。
    'ink': (13, 18, 28), 'panel': (24, 34, 46), 'panel2': (43, 58, 67),
    'acid': (181, 255, 82), 'portal': (83, 244, 190), 'violet': (157, 105, 236),
    'warning': (255, 181, 58), 'grid': (64, 91, 94), 'sky': (25, 42, 62),
    'paper': (220, 238, 198), 'ink2': (8, 12, 18),
}
FOV = math.pi / 3
MAP = ['1'*28] + ['1'+'0'*26+'1' for _ in range(26)] + ['1'*28]
PLAYER_RADIUS = .18
BULLET_RADIUS = .035


def bullet_hits_player(start, end, player_start, player_end, projectile_radius=BULLET_RADIUS):
    """Swept relative collision: both the projectile and player can move."""
    x,y=start[0]-player_start[0],start[1]-player_start[1]
    vx=(end[0]-player_end[0])-x; vy=(end[1]-player_end[1])-y
    t=max(0,min(1,-(x*vx+y*vy)/max(1e-12,vx*vx+vy*vy)))
    return math.hypot(x+vx*t,y+vy*t)<=PLAYER_RADIUS+projectile_radius


def make_sounds():
    """Generate short PCM effects locally; missing audio devices are supported."""
    sounds = {}
    try:
        if not pygame.mixer.get_init(): pygame.mixer.init(22050, -16, 1)
        rate, _, channels = pygame.mixer.get_init()
        rng = random.Random(7)
        for name,frequency,duration in [('shot',110,.12),('hit',750,.08),('melee_hit',980,.07),('sword_swing',210,.14),('boomerang_throw',520,.18),('spear_throw',130,.2),('dagger_dash',75,.12),('reload',320,.18),('insert',220,.15),('bolt',550,.12),('enemy',180,.25),('upgrade',880,.3),('ambient',65,3)]:
            samples = array('h')
            for i in range(int(rate*duration)):
                t=i/rate; envelope=(1-t/duration)**2
                tone=math.sin(2*math.pi*frequency*t*(1-.4*t/duration))
                noise=rng.uniform(-1,1)*(.8 if name=='shot' else .12)
                samples.extend([int(11000*envelope*(tone*.5+noise*.5))]*channels)
            sounds[name]=pygame.mixer.Sound(buffer=samples.tobytes())
            sounds[name].set_volume(.35)
        # Distinct boss cues: warning swell, heavy impact, claw sweep,
        # precision discharge, organic pulse and blade resonance.
        for name,freq,duration in [('charge',95,.8),('hammer',48,.55),('hunt',180,.3),('snipe',850,.25),('brood',130,.65),('duel',420,.4)]:
            samples=array('h')
            for i in range(int(rate*duration)):
                t=i/rate; progress=t/duration
                envelope=progress*.8 if name=='charge' else (1-progress)**2
                tone=math.sin(2*math.pi*freq*t*(1+.5*progress))
                value=int(18000*envelope*(tone*.65+rng.uniform(-1,1)*.25))
                samples.extend([value]*channels)
            sounds['boss_'+name]=pygame.mixer.Sound(buffer=samples.tobytes())
            sounds['boss_'+name].set_volume(.5)
        # Distinct timbres and envelopes for each weapon; no external audio needed.
        for index,freq,duration,gain in [(0,240,.065,.32),(1,65,.32,.48),(2,100,.13,.4),(3,45,.48,.5)]:
            samples=array('h')
            for i in range(int(rate*duration)):
                t=i/rate
                attack=math.exp(-t/(duration*.24))
                crack=rng.uniform(-1,1)*math.exp(-t/(.008 if index==3 else .018))
                bass=math.sin(2*math.pi*freq*t*(1-.3*t/duration))*attack
                metal=math.sin(2*math.pi*(1400 if index==0 else 650)*t)*math.exp(-t/.025)*.2
                value=int(max(-1,min(1,crack*.65+bass*.55+metal))*26000)
                samples.extend([value]*channels)
            sounds[f'shot{index}']=pygame.mixer.Sound(buffer=samples.tobytes())
            sounds[f'shot{index}'].set_volume(gain)
    except pygame.error:
        pass
    bolt_path=Path(__file__).resolve().parent/'Assets/audio/sniper_bolt.wav'
    if pygame.mixer.get_init() and bolt_path.is_file():
        try:
            sounds['sniper_bolt']=pygame.mixer.Sound(str(bolt_path))
            sounds['sniper_bolt'].set_volume(.65)
        except (pygame.error,OSError):
            pass
    machinegun_path=Path(__file__).resolve().parent/'Assets/audio/machinegun_shot.wav'
    if pygame.mixer.get_init() and machinegun_path.is_file():
        try:
            sounds['shot2']=pygame.mixer.Sound(str(machinegun_path))
            sounds['shot2'].set_volume(.4)
        except (pygame.error,OSError):
            pass
    reload_path=Path(__file__).resolve().parent/'Assets/audio/gun_reload.wav'
    if pygame.mixer.get_init() and reload_path.is_file():
        try:
            sounds['reload']=pygame.mixer.Sound(str(reload_path))
            sounds['reload'].set_volume(.55)
        except (pygame.error,OSError):
            pass
    smg_path=Path(__file__).resolve().parent/'Assets/audio/smg_shot.wav'
    if pygame.mixer.get_init() and smg_path.is_file():
        try:
            sounds['shot0']=pygame.mixer.Sound(str(smg_path))
            sounds['shot0'].set_volume(.4)
        except (pygame.error,OSError):
            pass
    sniper_path=Path(__file__).resolve().parent/'Assets/audio/sniper_shot.wav'
    if pygame.mixer.get_init() and sniper_path.is_file():
        try:
            sounds['shot3']=pygame.mixer.Sound(str(sniper_path))
            sounds['shot3'].set_volume(.5)
        except (pygame.error,OSError):
            pass
    boomerang_path=Path(__file__).resolve().parent/'Assets/audio/boomerang_throw.wav'
    if pygame.mixer.get_init() and boomerang_path.is_file():
        try:
            sounds['boomerang_throw']=pygame.mixer.Sound(str(boomerang_path))
            sounds['boomerang_throw'].set_volume(.5)
        except (pygame.error,OSError):
            pass
    spear_path=Path(__file__).resolve().parent/'Assets/audio/spear_throw.wav'
    if pygame.mixer.get_init() and spear_path.is_file():
        try:
            sounds['spear_throw']=pygame.mixer.Sound(str(spear_path))
            sounds['spear_throw'].set_volume(.5)
        except (pygame.error,OSError):
            pass
    return sounds

def wall(x, y):
    return y < 0 or y >= len(MAP) or x < 0 or x >= len(MAP[0]) or MAP[y][x] == "1"

def line_of_sight(x0, y0, x1, y1):
    """Return whether a shot can reach a target without crossing a wall."""
    distance = math.hypot(x1 - x0, y1 - y0)
    steps = max(1, int(distance / 0.04))
    for i in range(1, steps + 1):
        t = i / steps
        if wall(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t)):
            return False
    return True


def ray_wall_distance(x, y, dx, dy):
    """Traverse map cells exactly instead of taking hundreds of tiny steps."""
    cell_x, cell_y = math.floor(x), math.floor(y)
    step_x, step_y = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    delta_x = abs(1 / dx) if abs(dx) > 1e-12 else math.inf
    delta_y = abs(1 / dy) if abs(dy) > 1e-12 else math.inf
    side_x = (cell_x + 1 - x if dx >= 0 else x - cell_x) * delta_x
    side_y = (cell_y + 1 - y if dy >= 0 else y - cell_y) * delta_y
    for _ in range(128):
        if side_x < side_y:
            distance = side_x; side_x += delta_x; cell_x += step_x
        else:
            distance = side_y; side_y += delta_y; cell_y += step_y
        if wall(cell_x, cell_y):
            return max(.02, distance), cell_x, cell_y
    return 40., cell_x, cell_y

class Game:
    def __init__(self, show_menu=False, muted=False):
        pygame.init(); pygame.display.set_caption("异星实验场 · 无限强化")
        self.screen = pygame.display.set_mode((W, H)); self.clock = pygame.time.Clock()
        self.map_art=MapArt()
        self._background_cache={}
        self.enemy_art=EnemyArt()
        self._enemy_motion={}
        self.cloud_art=CloudArt()
        self.corpses=[]
        self.damage_popups=[]
        self.kill_streak=0; self.streak_until=0
        self.kill_methods={}; self.streak_methods={"headshot":0,"melee":0}
        self.player = [14., 14.]; self.angle = 0.0; self.pitch = 0.0; self.hp = 100
        self.z = 0.0; self.vertical_velocity = 0.0; self.gravity = 18.0; self.jump_height = .65
        self.on_ground=True; self.melee_cooldown=0; self.guarding=False; self.guard_damage_reduction=0.0
        # Pet system: one active companion, obtained/upgraded during runs.
        self.pet={'x':13.,'y':14.,'cooldown':0.0,'type':'none','level':0,'hp':60.,'max_hp':60.,'revive':0.0}
        self.pet_types=('healer','taunter','gunner','minelayer','berserker')
        self.pet_cooldown=0.0; self.pet_skill_cooldown=0.0
        # v2 arena layout: these cells are the single source of truth for
        # both perspective rendering and collision/LOS.
        self.terrain_cells={(8,11),(9,11),(18,11),(13,7),(13,8),(20,15)}; self.terrain=list(self.terrain_cells); self.wall_height=.42; self.terrain_phase=-1
        self.lava_cells={(10,10),(11,10),(10,11),(11,11),(16,16),(17,16),(16,17),(17,17),(18,17)}
        self.wave_event=None; self.wave_event_type='start'
        self.sounds = make_sounds(); self.muted = muted
        self.reload_sound_cache={}; self.reload_channel=None
        self.smg_sound_cache={}
        self.music_loaded = False
        music_path = Path(__file__).resolve().parent / 'assets' / 'audio' / 'kiravale-gaming-music-593659.mp3'
        try:
            if pygame.mixer.get_init() and music_path.is_file():
                pygame.mixer.music.load(str(music_path))
                pygame.mixer.music.set_volume(0 if muted else .3)
                pygame.mixer.music.play(-1, fade_ms=800)
                self.music_loaded = True
        except (pygame.error, OSError):
            pass
        self.projectiles = []; self.tracers = []; self.walk_phase = 0
        self.attack_animations = {}
        self.combat = CombatSystem(self)
        self.mag, self.reserve, self.mag_size = 12, 60, 12
        self.reserve_max=300
        self.ammo_station=(14.,10.)
        self.next_shot = 0; self.reload_until = 0; self.muzzle_until = 0; self.hit_until = 0
        self.weapon_action_start=-100000
        self.sniper_bolt_at=None
        self.max_hp = 100; self.damage = 25; self.fire_delay = 200
        self.move_speed = 3.2; self.reload_duration = 1300
        self.regen = 0; self.leech = 0; self.pierce = 0; self.blast = 0
        self.weapon_level = 1
        self.weapon_index=0; self.ads=False; self.boss_rewards=0
        self.weapon_ammo={}; self.weapon_ready=False
        self.unlocked_weapons={0}
        self.weapon_slots=[0]
        self.weapon_usage=[0.0]*len(WEAPONS)
        self.melee_heal_ready=0
        self.melee_staggers={}
        self.damage_bonus=1.; self.rate_bonus=1.; self.mag_bonus=0; self.reload_bonus=1.
        self.extras={}; self.shield=0; self.effects={}
        self.level = 1; self.xp = 0; self.xp_needed = 3; self.kills = 0
        self.upgrade_stacks = {}; self.choices = []; self.wave = 1
        self.now = 0; self.wave_wait = 0; self.damage_until = 0
        self.state = "playing"; self.message = "清除敌人获得经验，升级选择强化"
        self.font = load_font(21)
        self.big_font = load_font(34)
        self.card_font = load_font(18)
        self.enemies = []; self.spawn_wave()
        self.switch_weapon(0); self.begin_wave()
        self.focused = True
        self.pause_from = 'playing'
        if show_menu:
            self.state = 'menu'

    def begin_wave(self):
        self.state='wave'; self.wave_deadline=pygame.time.get_ticks()+3000
        # The preparation banner is still interactive: keep keyboard movement
        # available and only release the mouse aim capture.
        self._capture_mouse(False)

    def pause(self):
        if self.state not in ('playing', 'wave'):
            return
        self.pause_from = self.state
        if self.reload_channel: self.reload_channel.pause()
        self.wave_remaining = max(0, self.wave_deadline-pygame.time.get_ticks()) if self.state=='wave' else 0
        self.state = 'paused'
        self._capture_mouse(False)

    def resume(self):
        self.state = self.pause_from
        if self.reload_channel: self.reload_channel.unpause()
        if self.state == 'wave':
            self.wave_deadline = pygame.time.get_ticks() + self.wave_remaining
        self._capture_mouse(self.state == 'playing')

    def switch_weapon(self,index,refill=False):
        if index not in self.unlocked_weapons: return
        same_weapon = self.weapon_ready and index == self.weapon_index
        reload_end = self.reload_until if same_weapon and not refill else 0
        if self.weapon_ready: self.weapon_ammo[self.weapon_index]=self.mag
        self.weapon_index=index; w=WEAPONS[index]
        bonus=self.extras
        power_keys=('', 'shot_power', 'mg_power', 'sniper_power','melee_power','melee_power','melee_power','melee_power')
        haste_keys=('smg_haste', '', '', 'sniper_haste')
        pkey=power_keys[index] if index < len(power_keys) else ''
        hkey=haste_keys[index] if index < len(haste_keys) else ''
        self.damage=w['damage']*self.damage_bonus*(1+bonus.get(pkey,0))
        melee_haste=1+bonus.get('melee_haste',0) if w.get('kind') in ('melee','shield') else 1
        self.fire_delay=max(35,w['delay']/self.rate_bonus/(1+bonus.get(hkey,0))/melee_haste)
        # Switching weapons must start from the weapon's authored cadence;
        # stale cooldowns made the initial attack appear too slow or too fast.
        self.next_shot = min(getattr(self,'next_shot',0), self.now)
        self.mag_size=min(500,w['mag']+self.mag_bonus+(int(bonus.get('smg_mag',0)) if index==0 else 0))
        self.mag=self.mag_size if refill else min(self.mag_size,self.weapon_ammo.get(index,self.mag_size))
        self.weapon_ready=True
        self.reload_duration=max(250,w['reload']/self.reload_bonus/(1+bonus.get('mg_reload',0) if index==2 else 1))
        self.reload_until=reload_end
        if not same_weapon:
            if self.reload_channel: self.reload_channel.stop()
            self.sniper_bolt_at=None
            self.weapon_action_start=-100000
            self.muzzle_until=0
            self.reload_start=0
            self.guarding=False
            self.melee_cooldown=0
            if hasattr(self,'combat'):
                self.combat.cooldown=0
                self.combat.guard=False
                self.combat.active.clear()

    def switch_slot(self, slot):
        if 0 <= slot < len(self.weapon_slots):
            self.switch_weapon(self.weapon_slots[slot])

    def melee_attack(self, now=None):
        now=self.now if now is None else now
        if now<self.melee_cooldown or WEAPONS[self.weapon_index].get('kind') not in ('melee','shield'): return False
        self.melee_cooldown=now+self.fire_delay; self.shoot(now); return True

    def jump(self):
        if self.on_ground:
            self.vertical_velocity=math.sqrt(2*self.gravity*self.jump_height); self.on_ground=False; return True
        return False

    # Compatibility alias used by external QA tools.
    def jump_action(self):
        return self.jump()

    def terrain_blocks(self,x0,y0,x1,y1,z=0):
        steps=max(1,int(math.hypot(x1-x0,y1-y0)*10))
        return any(wall(int(x0+(x1-x0)*i/steps),int(y0+(y1-y0)*i/steps)) or (z<self.wall_height and (int(x0+(x1-x0)*i/steps),int(y0+(y1-y0)*i/steps)) in self.terrain_cells) for i in range(steps+1))

    def world_los(self,x0,y0,x1,y1,z0=0,z1=0):
        steps=max(1,int(math.hypot(x1-x0,y1-y0)*12))
        for i in range(1,steps+1):
            t=i/steps; x=x0+(x1-x0)*t; y=y0+(y1-y0)*t; z=z0+(z1-z0)*t
            if wall(int(x),int(y)): return False
            if (int(x),int(y)) in self.terrain_cells and z<self.wall_height: return False
        return True

    def world_los(self,x0,y0,x1,y1):
        """Line of sight used by melee and boss abilities; dynamic walls block it."""
        return not self.terrain_blocks(x0,y0,x1,y1,0.2)

    def update_pet(self,dt,now):
        if not self.pet: return
        if self.pet.get('type')=='none': return
        # Revive timer for taunter/gunner companions.
        if self.pet['hp']<=0:
            self.pet['revive']=max(0.0,self.pet.get('revive',0)-dt)
            if self.pet['revive']<=0: self.pet['hp']=self.pet['max_hp']
            return
        if self.pet.get('wave')!=self.wave:
            self.pet.update(wave=self.wave,x=self.player[0]-1,y=self.player[1])
        if self.pet.get('type')!='taunter':
            self.pet['x']+=(self.player[0]-1-self.pet['x'])*min(1,dt*4)
            self.pet['y']+=(self.player[1]-self.pet['y'])*min(1,dt*4)
        typ=self.pet.get('type','gunner'); self.pet_cooldown=max(0,self.pet_cooldown-dt*1000); self.pet_skill_cooldown=max(0,self.pet_skill_cooldown-dt*1000)
        target=min(self.enemies,key=lambda e:math.hypot(e[0]-self.pet['x'],e[1]-self.pet['y']),default=None)
        if typ=='healer' and self.pet_skill_cooldown<=0:
            self.pet['animation_start']=now
            self.hp=min(self.max_hp,self.hp+4*self.pet['level']); self.pet_skill_cooldown=5000
        elif typ=='berserker' and self.pet_skill_cooldown<=0:
            self.pet['animation_start']=now
            self.pet['rage_until']=now+2500; self.pet_skill_cooldown=7000
        elif typ=='minelayer' and self.pet_skill_cooldown<=0:
            self.pet['animation_start']=now
            self.pet_skill_cooldown=3500
            self.pet.setdefault('mines',[]).append([self.pet['x'],self.pet['y'],now+12000])
        elif typ=='gunner' and target and self.pet_cooldown<=0 and math.hypot(target[0]-self.pet['x'],target[1]-self.pet['y'])<8 and self.world_los(self.pet['x'],self.pet['y'],target[0],target[1]):
            self.pet['animation_start']=now
            self.damage_enemy(target,10*self.pet['level'],now,120); self.pet_cooldown=900
        for mine in list(self.pet.get('mines',[])):
            nearby=[e for e in self.enemies if e[2]>0 and math.hypot(e[0]-mine[0],e[1]-mine[1])<1.3]
            if nearby:
                for e in nearby: self.damage_enemy(e,35*self.pet['level'],now,250)
            if nearby or now>=mine[2]: self.pet['mines'].remove(mine)

    def offer_pet_upgrade(self):
        names={'healer':'环绕治疗精灵','taunter':'定点诱饵守卫','gunner':'机枪无人机','minelayer':'布雷巡逻犬','berserker':'狂暴增益精灵'}
        descriptions={'healer':'每 5 秒恢复生命，升级提高治疗量','taunter':'每波原地驻守，吸引近处敌人，有血量和 15 秒复活','gunner':'每 0.9 秒自动攻击，承受仇恨，15 秒复活','minelayer':'每 3.5 秒留下一枚仅伤敌人的地雷','berserker':'每 7 秒激发 2.5 秒狂暴，提升伤害'}
        current=self.pet.get('type','none')
        typ=current if current!='none' and random.random()<.65 else random.choice(self.pet_types)
        title=('升级·' if typ==current else '获得·')+names[typ]
        if random.random()<.45 or self.wave%5==0:
            old_rank=self.choices[0][3]; old_scale=self.choices[0][4]
            self.choices[0]=('pet_'+typ,title,descriptions[typ],old_rank,old_scale)

    def choose_pet_upgrade(self,key):
        if not key.startswith('pet_'): return False
        typ=key[4:]
        if typ not in self.pet_types: return False
        level=min(10,self.pet.get('level',0)+1) if self.pet.get('type')==typ else 1
        self.pet.update(type=typ,level=level,hp=60+20*level,max_hp=60+20*level,revive=0,x=self.player[0]-1,y=self.player[1],mines=[])
        return True

    def acquire_weapon(self, index):
        if index in self.unlocked_weapons or len(self.weapon_slots) >= 3:
            return False
        self.weapon_slots.append(index)
        self.unlocked_weapons.add(index)
        self.switch_weapon(index)
        return True

    def hurt(self,amount):
        current=WEAPONS[self.weapon_index]
        if current.get('kind') in ('melee','shield'):
            amount*=1-min(.4,self.extras.get('melee_armor',0))
        if self.guarding: amount*=1-min(.75,self.guard_damage_reduction+self.extras.get('melee_guard',0))
        if current.get('kind')=='shield':
            amount*=max(0.0,1-current.get('block',0))
        if random.random()<min(.5,self.extras.get('dodge',0)): return
        amount*=1-min(.7,self.extras.get('armor',0))
        absorbed=min(self.shield,amount); self.shield-=absorbed
        self.hp=max(0,self.hp-(amount-absorbed)); self.damage_until=self.now+180

    def damage_enemy(self, enemy, amount, now, flash=180, method="normal"):
        """Apply actual health loss and attach feedback to the damaged target."""
        actual=min(max(0,enemy[2]),max(0,amount))
        if actual<=0: return 0
        enemy[2]-=actual
        if enemy[2]<=0: self.kill_methods[id(enemy)]=method
        enemy[3]=max(enemy[3],now+flash)
        self.damage_popups=[p for p in self.damage_popups if p['end']>now][-95:]
        recent=next((p for p in reversed(self.damage_popups) if p['target'] is enemy and now-p['start']<120),None)
        if recent:
            recent['amount']+=actual; recent['end']=now+850
        else:
            self.damage_popups.append(dict(target=enemy,amount=actual,start=now,end=now+850))
        return actual

    def finish_kills(self,now):
        dead=[e for e in self.enemies if e[2]<=0]
        if not dead:
            return
        self.enemies=[e for e in self.enemies if e[2]>0]
        for enemy in dead:
            self.corpses.append((enemy.copy(),now+(3200 if enemy[5]=='boss' else 1800)))
            self.effects.pop(id(enemy),None)
            self.melee_staggers.pop(id(enemy),None)
            self.attack_animations.pop(id(enemy),None)
            self._enemy_motion.pop(id(enemy),None)
        self.boss_rewards+=sum(e[5]=='boss' for e in dead)
        self.kills+=len(dead)
        if now>self.streak_until:
            self.kill_streak=0; self.streak_methods={"headshot":0,"melee":0}
        self.kill_streak+=len(dead)
        for enemy in dead:
            method=self.kill_methods.pop(id(enemy),'normal')
            if method in self.streak_methods: self.streak_methods[method]+=1
        self.streak_until=now+1000
        names=('一杀','二杀','三杀','四杀','五杀','六杀')
        title=names[self.kill_streak-1] if self.kill_streak<=6 else '杀敌如麻'
        self.kill_popup=(f'{title}  ·  {self.kill_streak} 连杀',now+1800)
        self.xp+=sum(12 if e[5]=='boss' else 5 if e[5]=='elite' else 1 for e in dead)*(1+self.extras.get('xp',0))
        self.hp=min(self.max_hp,self.hp+len(dead)*self.leech)
        self.reserve+=math.ceil(len(dead)*self.extras.get('supply',0))
        blue=len(dead)
        orange=len(dead)
        if blue and self.extras.get('blue_supply',0):
            self.reserve+=math.ceil(blue*self.extras['blue_supply'])
            self.message='稀有强化触发：击杀获得备弹'
        if orange and self.extras.get('orange_reset',0):
            self.next_shot=now
            self.orange_until=now+2000
            self.message='史诗强化触发：击杀刷新扳机冷却'
        self.reserve=min(self.reserve_max,self.reserve)
        if not self.enemies: self.wave_wait=now+100
        if self.boss_rewards or self.xp>=self.xp_needed:
            if self.boss_rewards: self.boss_rewards-=1; self.offer_upgrade(True)
            else: self.level_up()

    def _capture_mouse(self, capture):
        if not capture:
            self.ads = False
        pygame.event.set_grab(capture); pygame.mouse.set_visible(not capture)
        pygame.mouse.get_rel()

    def sound(self, name):
        if not self.muted and name in self.sounds:
            if name=='shot0' and pygame.mixer.get_init():
                import numpy as np
                # Keep the attack at its original pitch; shorten only the tail
                # to fit the actual cadence, including temporary haste.
                duration=max(35,min(700,int(self.next_shot-self.weapon_action_start)))
                if duration not in self.smg_sound_cache:
                    samples=pygame.sndarray.array(self.sounds[name])
                    count=min(len(samples),max(1,int(pygame.mixer.get_init()[0]*duration/1000)))
                    data=samples[:count].copy()
                    fade=min(count,max(1,int(pygame.mixer.get_init()[0]*.005)))
                    ramp=np.linspace(1,0,fade)
                    if data.ndim>1: ramp=ramp[:,None]
                    data[-fade:]=(data[-fade:]*ramp).astype(data.dtype)
                    clip=pygame.sndarray.make_sound(np.ascontiguousarray(data)); clip.set_volume(.4)
                    if len(self.smg_sound_cache)>=24: self.smg_sound_cache.pop(next(iter(self.smg_sound_cache)))
                    self.smg_sound_cache[duration]=clip
                for clip in self.smg_sound_cache.values(): clip.stop()
                self.smg_sound_cache[duration].play()
                return
            if name in ('shot2','shot3','sniper_bolt','boomerang_throw','spear_throw'): self.sounds[name].stop()
            if name=='shot3' and 'sniper_bolt' in self.sounds:
                self.sounds['sniper_bolt'].stop()
            self.sounds[name].play()

    def play_reload_audio(self):
        """Resample the complete user recording to the active reload duration."""
        if self.muted or 'reload' not in self.sounds or not pygame.mixer.get_init(): return
        import numpy as np
        duration=int(self.reload_duration)
        if duration not in self.reload_sound_cache:
            samples=pygame.sndarray.array(self.sounds['reload'])
            count=max(1,round(pygame.mixer.get_init()[0]*duration/1000))
            positions=np.linspace(0,len(samples)-1,count)
            source=np.arange(len(samples))
            data=(np.interp(positions,source,samples) if samples.ndim==1 else
                  np.stack([np.interp(positions,source,samples[:,i]) for i in range(samples.shape[1])],axis=1))
            sound=pygame.sndarray.make_sound(np.ascontiguousarray(data.astype(samples.dtype)))
            sound.set_volume(.55)
            if len(self.reload_sound_cache)>=16: self.reload_sound_cache.pop(next(iter(self.reload_sound_cache)))
            self.reload_sound_cache[duration]=sound
        if self.reload_channel: self.reload_channel.stop()
        self.reload_channel=self.reload_sound_cache[duration].play()

    def near_ammo_station(self):
        return math.hypot(self.player[0]-self.ammo_station[0],self.player[1]-self.ammo_station[1])<=1.8

    def refill_reserve(self):
        if self.state=='playing' and self.near_ammo_station():
            self.reserve=self.reserve_max
            self.message='弹药补给：备弹已补满'
            self.sound('insert')

    def reset(self):
        muted = self.muted
        self.__init__(muted=muted)
        self.muted = muted
        if self.music_loaded:
            pygame.mixer.music.set_volume(0 if muted else .3)

    def move(self, dx, dy):
        # A body radius and substeps prevent corner clipping and tunnelling.
        steps = max(1, math.ceil(math.hypot(dx, dy) / .1))
        for _ in range(steps):
            for axis, delta in ((0, dx / steps), (1, dy / steps)):
                pos = self.player.copy(); pos[axis] += delta
                # Once standing on a raised block, allow the body to move off
                # its edge. The old corner test kept one foot overlapping the
                # block forever, trapping the player on top.
                if all(not wall(math.floor(pos[0]+ox), math.floor(pos[1]+oy)) and
                       (self.z>=self.wall_height or (math.floor(pos[0]+ox), math.floor(pos[1]+oy)) not in self.terrain_cells)
                       for ox in (-.18,.18) for oy in (-.18,.18)):
                    self.player = pos

    def spawn_wave(self):
        self.combat.boss_pattern.clear(); self.combat.boss_cycles.clear()
        self.combat.boss_impacts.clear()
        self.combat.throws.clear(); self.combat.active.clear()
        self.corpses.clear()
        self.projectiles.clear(); self.tracers.clear(); self.effects.clear()
        self.attack_animations.clear()
        spots = [(x+.5,y+.5) for y,row in enumerate(MAP) for x,c in enumerate(row)
                 if c=='0' and self.enemy_position_clear(x+.5,y+.5) and 6 < math.hypot(x+.5-self.player[0],y+.5-self.player[1]) < 13]
        random.shuffle(spots)
        count=min(3+self.wave,24,len(spots))
        special='boss' if self.wave%5==0 else 'elite' if self.wave%3==0 else None
        kinds=[random.choice(['normal','runner']) for _ in range(count)]
        # At most a quarter are shooters, plus one special enemy.
        ranged_count=min(count//4,4) if self.wave>=2 else 0
        ranged_slots=random.sample(list(range(1,count)),ranged_count)
        for index in ranged_slots: kinds[index]='shooter'
        if self.wave>=3 and ranged_slots: kinds[ranged_slots[-1]]='bat'
        if special: kinds[0]=special
        boss_design=None
        if self.wave%5==0:
            from rogue_content import BOSS_DESIGNS
            boss_design=BOSS_DESIGNS[(self.wave//5-1)%len(BOSS_DESIGNS)]
        for i in range(count):
            kind=kinds[i]
            # Controlled linear scaling prevents infinite-wave exponential spikes.
            base = BALANCE['enemy_base_hp'] + BALANCE['enemy_hp_per_wave'] * self.wave
            scale = min(BALANCE['max_wave_hp_scale'], 1 + self.wave / 35)
            boss_scale=boss_design['hp'] if kind=='boss' and boss_design else 1
            hp = base * scale * boss_scale * (BALANCE['boss_multiplier'] if kind=='boss' else BALANCE['elite_multiplier'] if kind=='elite' else BALANCE['runner_multiplier'] if kind=='runner' else 1)
            x,y = spots[i]
            self.enemies.append([x,y,hp,0,hp,kind,0])
        self.mag = self.mag_size; self.reserve = min(self.reserve_max,max(self.reserve, math.ceil(sum(e[4] for e in self.enemies)/self.damage)*3+self.mag_size*4))
        self.shield=self.extras.get('shield',0)
        self.wave_event_type='boss' if self.wave%5==0 else 'elite' if self.wave%3==0 else 'start'
        self.wave_event=f'wave_{self.wave_event_type}'
        title=boss_design['name'] if boss_design else 'Boss'
        self.message = f'第 {self.wave} 波开始' + (f' · {title} 来袭！' if self.wave%5==0 else '')

    def upgrade_weight(self,key):
        total=sum(self.weapon_usage)
        if total<=0: return 1
        owners=[weapon for special,_,_,weapon in SPECIALS if special==key]
        if key.startswith('melee_'):
            share=sum(self.weapon_usage[4:])/total
        elif owners:
            share=sum(self.weapon_usage[i] for i in owners)/total
        else: return 1
        return 1+6*share

    def offer_upgrade(self,boss=False):
        self.reward_is_boss=boss; self.choices=[]
        for _ in range(3):
            rank=random.choices(range(4),weights=(0,5,45,50) if boss else (60,28,10,2))[0]
            eligible={key for key,_,_,weapon in SPECIALS if weapon in self.unlocked_weapons or
                      (key.startswith('melee_') and any(i>=4 for i in self.unlocked_weapons))}
            eligible.add('orange_reset')
            if 4 not in self.unlocked_weapons: eligible.discard('melee_guard')
            special_keys={item[0] for item in SPECIALS}
            chosen_keys={u[0] for u in self.choices}
            pool=[u for u in ALL_UPGRADES if u[3]==rank and u[0] not in chosen_keys and (u[0] not in special_keys or u[0] in eligible)]
            self.choices.append(random.choices(pool,weights=[self.upgrade_weight(u[0]) for u in pool])[0])
        locked=[i for i in range(len(WEAPONS)) if i not in self.unlocked_weapons] if len(self.weapon_slots)<3 else []
        # Empty slots strongly favor a clearly labelled weapon offer, while
        # still leaving room for normal upgrades.
        if locked and not boss and random.random()<.70:
            index=random.choice(locked)
            self.choices[2]=(f'unlock{index}',f'获得·{WEAPONS[index]["name"]}',f'加入武器槽 {len(self.weapon_slots)+1}：获得后按 {len(self.weapon_slots)+1} 切换',1,1)
        self.offer_pet_upgrade()
        self.sound('upgrade')
        self.state = 'upgrade'; self._capture_mouse(False)

    def choose_upgrade(self, index):
        if self.state != 'upgrade' or not 0 <= index < len(self.choices): return
        key,title,_,rank,scale = self.choices[index]
        self.upgrade_stacks[key] = self.upgrade_stacks.get(key,0)+1
        if key in HYBRID_CARDS:
            for component in HYBRID_CARDS[key][1:]:
                amount=scale*.6
                if component=='health': self.max_hp+=int(15*amount); self.hp=min(self.max_hp,self.hp+25*amount)
                elif component=='regen': self.regen+=.3*amount
                elif component=='leech': self.leech+=2*amount
                elif component=='speed': self.move_speed=min(8,self.move_speed*(1+.06*amount))
                elif component=='reload': self.reload_bonus=min(100,self.reload_bonus*(1+.1*amount))
                elif component=='haste': self.rate_bonus=min(100,self.rate_bonus*(1+.1*amount))
                elif component=='power': self.damage_bonus*=1+.12*amount
                elif component=='magazine': self.mag_bonus+=int(3*amount)
                elif component=='pierce': self.pierce+=max(1,int(amount))
                elif component=='blast': self.blast+=.12*amount
                else:
                    values=dict(armor=.04,crit=.05,burn=3,poison=2,slow=.1,critpower=.2,range=.15,shield=15,execute=.2,xp=.1)
                    self.extras[component]=self.extras.get(component,0)+values[component]*amount
        elif self.choose_pet_upgrade(key): pass
        elif key.startswith('unlock'):
            weapon=int(key.removeprefix('unlock')); self.acquire_weapon(weapon)
        elif key=='power': self.damage_bonus *= 1+.12*scale
        elif key=='haste': self.rate_bonus = min(100,self.rate_bonus*(1+.10*scale))
        elif key=='health': self.max_hp += int(15*scale); self.hp = min(self.max_hp,self.hp+25*scale)
        elif key=='speed': self.move_speed = min(8,self.move_speed*(1+.06*scale))
        elif key=='magazine': self.mag_bonus += int(3*scale)
        elif key=='reload': self.reload_bonus = min(100,self.reload_bonus*(1+.10*scale))
        elif key=='regen': self.regen += .3*scale
        elif key=='leech': self.leech += 2*scale
        elif key=='pierce': self.pierce += max(1,int(scale))
        elif key=='blast': self.blast += .12*scale
        elif key=='heal': self.hp=min(self.max_hp,self.hp+30*scale)
        else:
            amounts={'crit':.05,'critpower':.2,'armor':.04,'dodge':.03,'slow':.1,'burn':3,'poison':2,'execute':.2,'range':.15,'pellets':1,'supply':2,'xp':.1,'knockback':.2,'shield':15,'smg_haste':.18,'smg_mag':8,'shot_tight':.2,'shot_power':.2,'mg_power':.18,'mg_reload':.25,'sniper_power':.25,'sniper_haste':.2,
                     # Melee-specific cards are applied through switch_weapon/combat_system.
                     'melee_power':.20,'melee_haste':.15,'sword_arc':.25,'boomerang_return':.35,'spear_pierce':.45,'dagger_dash':.30}
            amounts.update(blue_supply=8,orange_reset=.08,melee_armor=.08,melee_sustain=1,
                           melee_regen=.5,melee_reach=.15,melee_guard=.10,melee_stagger=.15)
            self.extras[key]=self.extras.get(key,0)+amounts.get(key,0)*scale
        self.message = f'已获得：{title} ×{self.upgrade_stacks[key]}'
        self.switch_weapon(self.weapon_index,refill=key=='magazine')
        self.state='playing'; self._capture_mouse(True)
        if not self.focused:
            self.pause()
        if self.boss_rewards: self.boss_rewards-=1; self.offer_upgrade(True)
        elif self.xp >= self.xp_needed: self.level_up()

    def level_up(self):
        self.xp -= self.xp_needed; self.level += 1
        self.xp_needed = 3 + self.level//2
        self.offer_upgrade()

    def shoot(self, now):
        # Allow movement during the three-second wave countdown; combat and
        # weapon timers remain synchronized with the active state.
        if self.state not in ("playing", "wave"): return
        if now < self.next_shot or now < self.reload_until: return
        w=WEAPONS[self.weapon_index]
        is_melee=w.get('kind') in ('melee','shield')
        if not is_melee and self.mag <= 0: self.reload(now); return
        burst_bonus=self.extras.get('orange_reset',0) if now<getattr(self,'orange_until',0) else 0
        if not is_melee: self.mag -= 1
        self.next_shot = now + max(35,self.fire_delay/(1+burst_bonus))
        self.weapon_action_start=now
        self.sound(f'shot{self.weapon_index}')
        if self.weapon_index==3:
            self.sniper_bolt_at=now+min(220,max(35,int(self.fire_delay*.2)))
        targets = []; w=WEAPONS[self.weapon_index]
        if w.get('kind') in ('melee','shield'):
            arc=w.get('arc',.8)
            for e in self.enemies:
                dx,dy=e[0]-self.player[0],e[1]-self.player[1]; dist=math.hypot(dx,dy)
                rel=abs((math.atan2(dy,dx)-self.angle+math.pi)%(2*math.pi)-math.pi)
                if dist<=w['range'] and rel<=arc/2 and line_of_sight(*self.player,e[0],e[1]): targets.append((dist,e))
            self.muzzle_until=now+100; self.tracers=[]
            for _,target in targets: self.damage_enemy(target,self.damage,now,method="melee")
            self.finish_kills(now)
            return
        count=min(64,w['pellets']+int(self.extras.get('pellets',0))) if self.weapon_index==1 else 1
        # Center pellet is guaranteed; the remaining pellets use a stable disk.
        spread=14/(1+self.extras.get('shot_tight',0))*(.65 if self.ads else 1)
        pellets=[(W//2,H//2)]
        for i in range(1,count):
            radius=spread*math.sqrt(i/max(1,count-1)); angle=i*2.399963
            pellets.append((W//2+math.cos(angle)*radius,H//2+math.sin(angle)*radius))
        visible_targets=[]
        for enemy in self.enemies:
            dist=math.hypot(enemy[0]-self.player[0],enemy[1]-self.player[1])
            if dist>=w['range']*(1+self.extras.get('range',0)) or not line_of_sight(*self.player,enemy[0],enemy[1]):
                continue
            visual=self.enemy_visual(enemy,hit_test=True)
            if visual:
                visible_targets.append((dist,enemy,visual))
        for aim in pellets:
          hits=[]
          for dist,e,visual in visible_targets:
            if visual:
                image,rect = visual
                point=(int(aim[0])-rect.x,int(aim[1])-rect.y)
                # The same opaque pixels are used to draw and hit-test enemies.
                if not rect.collidepoint(int(aim[0]),int(aim[1])) or image.get_at(point).a == 0: continue
                bounds=image.get_bounding_rect(min_alpha=128)
                # Head zone is the central upper quarter of the opaque body.
                head=(bounds.top<=point[1]<bounds.top+bounds.height*.25 and
                      abs(point[0]-bounds.centerx)<bounds.width*.28)
                hits.append((dist,e,head))
          # Close overlapping silhouettes must not absorb every distant shot.
          # Prefer the aimed distant target if a contact enemy also covers it.
          distant=[item for item in hits if item[0]>.85]
          candidates=distant if distant and any(item[0]<=.85 for item in hits) else hits
          targets.extend(sorted(candidates,key=lambda item:item[0])[:1+self.pierce])
        self.muzzle_until = now + 70
        distance = min((item[0] for item in targets),default=30)
        # Hitscan weapons communicate impact on the enemy, not a misleading screen-space ray.
        if targets: self.sound('hit')
        for _,target,head in targets:
            damage=self.damage*(1+.35*self.pet.get('level',0) if now<self.pet.get('rage_until',0) else 1)
            if random.random()<min(.8,self.extras.get('crit',0)): damage*=2+self.extras.get('critpower',0)
            if target[2]<target[4]*.3: damage*=1+self.extras.get('execute',0)
            self.damage_enemy(target,damage,now,method="headshot" if head else "normal"); self.hit_until = now+120
            self.effects[id(target)]=(now+2500,self.extras.get('burn',0)+self.extras.get('poison',0))
            dist=max(.01,math.hypot(target[0]-self.player[0],target[1]-self.player[1]))
            push=self.extras.get('knockback',0)
            nx=target[0]+(target[0]-self.player[0])/dist*push; ny=target[1]+(target[1]-self.player[1])/dist*push
            self.move_enemy(target,nx-target[0],ny-target[1])
            if self.blast:
                for other in self.enemies:
                    if other is not target and math.hypot(other[0]-target[0],other[1]-target[1])<1.8 and line_of_sight(target[0],target[1],other[0],other[1]):
                        self.damage_enemy(other,self.damage*self.blast,now)
        self.finish_kills(now)

    def reload(self, now):
        if WEAPONS[self.weapon_index].get('kind') in ('melee','shield'): return
        if self.mag < self.mag_size and self.reserve and not self.reload_until:
            self.reload_until = now + self.reload_duration
            self.sniper_bolt_at=None
            self.play_reload_audio()
            self.reload_start=now; self.reload_stage=0

    def update(self, dt, now):
        if self.state != "playing": return
        if self.sniper_bolt_at is not None and now>=self.sniper_bolt_at:
            self.sniper_bolt_at=None
            if self.weapon_index==3: self.sound('sniper_bolt')
        self.weapon_usage[self.weapon_index]+=dt
        if self.weapon_index>=4:
            self.hp=min(self.max_hp,self.hp+min(5,self.extras.get('melee_regen',0))*dt)
        phase=int(now//8000)%2
        if phase!=self.terrain_phase:
            self.terrain_phase=phase
            for cell in ((12,16),(16,12),(16,16)):
                # Never spawn a wall through the player's body.
                if phase and (math.floor(self.player[0]),math.floor(self.player[1]))!=cell: self.terrain_cells.add(cell)
                else: self.terrain_cells.discard(cell)
        ground=self.wall_height if (math.floor(self.player[0]),math.floor(self.player[1])) in self.terrain_cells else 0
        for enemy in self.enemies:
            self.unstuck_enemy(enemy)
        if self.z > ground or self.vertical_velocity != 0:
            self.vertical_velocity -= self.gravity * dt
            self.z += self.vertical_velocity * dt
            if self.z <= ground: self.z = ground; self.vertical_velocity = 0.0
            self.on_ground=self.z==ground
        self.update_pet(dt,now)
        self.combat.update(dt, now)
        # Lava zones are hazardous floor, but do not block movement.
        if self.z<=.08 and (math.floor(self.player[0]), math.floor(self.player[1])) in self.lava_cells:
            self.hurt((12 + self.wave * .4) * dt)
        if self.hp <= 0:
            self.state='lost'; self.message='本局结束'; self._capture_mouse(False)
            return
        if self.reload_until and not (Path(__file__).resolve().parent/'Assets/audio/gun_reload.wav').is_file():
            progress=(now-self.reload_start)/self.reload_duration
            if progress>=.45 and self.reload_stage==0: self.sound('insert'); self.reload_stage=1
            if progress>=.8 and self.reload_stage==1: self.sound('bolt'); self.reload_stage=2
        if self.reload_until and now >= self.reload_until:
            n = min(self.mag_size-self.mag, self.reserve); self.mag += n; self.reserve -= n; self.reload_until = 0
        self.hp = min(self.max_hp, self.hp+self.regen*dt)
        if self.wave_wait and now >= self.wave_wait:
            self.wave_wait=0
            if (self.wave+1)%5==0:
                self.pending_boss_wave=self.wave+1
                self.boss_intro_start=pygame.time.get_ticks()
                self.state='boss_intro'; self._capture_mouse(False)
                self.projectiles.clear(); self.combat.boss_pattern.clear()
                return
            self.wave += 1; self.wave_event='wave_start'; self.wave_event_type='wave_start'; self.spawn_wave(); self.begin_wave(); return
        keys = pygame.key.get_pressed(); speed = self.move_speed * dt
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]: speed *= 1.5
        forward = (keys[pygame.K_w] or keys[pygame.K_UP]) - (keys[pygame.K_s] or keys[pygame.K_DOWN])
        side = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        forward *= speed; side *= speed
        if forward and side: forward /= math.sqrt(2); side /= math.sqrt(2)
        if forward or side: self.walk_phase += dt*10
        player_start=self.player.copy()
        self.move(math.cos(self.angle)*forward + math.cos(self.angle+math.pi/2)*side,
                  math.sin(self.angle)*forward + math.sin(self.angle+math.pi/2)*side)
        for e in self.enemies:
            effect=self.effects.get(id(e))
            if effect and now<effect[0]: self.damage_enemy(e,effect[1]*dt,now,0)
            if e[2] <= 0:
                continue
            target_pos=self.player
            if self.pet.get('type') in ('taunter','gunner') and self.pet['hp']>0:
                pd=math.hypot(self.pet['x']-e[0],self.pet['y']-e[1])
                if pd< (6 if self.pet['type']=='taunter' else 2.5): target_pos=(self.pet['x'],self.pet['y'])
                if pd<.7:
                    self.pet['hp']-=dt*(10+self.wave)
                    if self.pet['hp']<=0: self.pet['revive']=15
            dx,dy=target_pos[0]-e[0],target_pos[1]-e[1]; d=math.hypot(dx,dy)
            animation=self.attack_animations.get(id(e))
            if animation and animation[0]=='melee' and now>=animation[1]:
                if d<.7 and line_of_sight(*self.player,e[0],e[1]):
                    self.hurt((8+self.wave*1.2)*(2 if e[5]=='boss' else 1)); self.sound('hit')
                self.attack_animations[id(e)]=('swing',now+180)
            elif animation and animation[0]!='melee' and now>=animation[1]:
                self.attack_animations.pop(id(e),None)
            if e[5] == 'boss' and now>=e[6] and id(e) not in self.combat.boss_pattern:
                self.combat.boss_attack(e, now)
                # Cooldown starts after recovery, preserving a real counterattack window.
                e[6]=self.combat.boss_pattern.get(id(e),{}).get('recover',now)+650
                self.sound('enemy')
                self.attack_animations[id(e)]=('fire',now+180)
            elif e[5] in ('shooter','bat') and d<22 and now>=e[6]:
                length=max(.01,d)
                aim=math.atan2(dy,dx)
                fan=(-.32,-.16,0,.16,.32) if e[5]=='boss' else (0,)
                for spread in fan:
                    height=.85 if e[5]=='bat' else 0.
                    self.projectiles.append([e[0],e[1],math.cos(aim+spread)*5,math.sin(aim+spread)*5,8+self.wave,now+7000,height,(self.z-height)/max(.3,d/5),'wave' if e[5]=='bat' else 'bullet'])
                e[6]=now+(1100 if e[5]=='boss' and e[2]<e[4]/2 else 1800 if e[5]=='boss' else 2200); self.sound('enemy')
                self.attack_animations[id(e)]=('fire',now+180)
            if d > (7 if e[5] in ('shooter','bat') else .45) and id(e) not in self.combat.boss_pattern:
                tx,ty=self.enemy_waypoint(e,target_pos)
                vx,vy=tx-e[0],ty-e[1]; length=max(.001,math.hypot(vx,vy))
                rate=(1.4 if e[5]=='runner' else .6 if e[5]=='tank' else .9)*(1+min(self.wave,40)*.015)
                if e[5]=='boss':
                    from rogue_content import BOSS_DESIGNS
                    rate*=BOSS_DESIGNS[(self.wave//5-1)%5]['speed']
                if now<self.melee_staggers.get(id(e),0): rate*=.7
                if e[3]>now: rate*=1-min(.75,self.extras.get('slow',0))
                step=min(rate*dt,length,max(0,d-.4)); ux,uy=vx/length,vy/length
                self.move_enemy(e,ux*step,uy*step)
            # Damage only when an enemy is actually adjacent and has a clear
            # path; otherwise an enemy behind a wall could hurt the player.
            if math.hypot(self.player[0]-e[0],self.player[1]-e[1]) < 0.55 and line_of_sight(self.player[0], self.player[1], e[0], e[1]):
                if now>=e[6] and id(e) not in self.combat.boss_pattern:
                    self.attack_animations[id(e)]=('melee',now+350)
                    e[6]=now+1000
        remaining=[]
        for p in self.projectiles:
            if now>=p[5]: continue
            oldx,oldy=p[0],p[1]; oldz=p[6] if len(p)>6 else 0.; p[0]+=p[2]*dt; p[1]+=p[3]*dt
            if len(p)>7: p[6]+=p[7]*dt
            bullet_z=p[6] if len(p)>6 else 0.
            if self.terrain_blocks(oldx,oldy,p[0],p[1],bullet_z): continue
            kind=p[8] if len(p)>8 else ''
            projectile_radius={'boss_colossus':.18,'boss_hunter':.07,'boss_judge':.06,'boss_weaver':.15,'boss_executioner':.14}.get(kind,BULLET_RADIUS)
            if abs(bullet_z-self.z)<.26 and bullet_hits_player((oldx,oldy),p[:2],player_start,self.player,projectile_radius):
                self.hurt(p[4]); self.sound('hit')
            elif now<p[5] and not wall(int(p[0]),int(p[1])): remaining.append(p)
        self.projectiles=remaining
        self.tracers=[t for t in self.tracers if now<t[6]]
        if self.hp <= 0:
            self.state = "lost"; self.message = "本局结束"; self._capture_mouse(False)
            return
        if any(e[2]<=0 for e in self.enemies): self.finish_kills(now)

    def enemy_position_clear(self,x,y):
        return all(not wall(math.floor(x+ox),math.floor(y+oy)) and
                   (math.floor(x+ox),math.floor(y+oy)) not in self.terrain_cells
                   for ox,oy in ((-.2,-.2),(-.2,.2),(.2,-.2),(.2,.2)))

    def move_enemy(self,enemy,dx,dy):
        start=tuple(enemy[:2])
        steps=max(1,math.ceil(math.hypot(dx,dy)/.08))
        for _ in range(steps):
            if self.enemy_position_clear(enemy[0]+dx/steps,enemy[1]): enemy[0]+=dx/steps
            if self.enemy_position_clear(enemy[0],enemy[1]+dy/steps): enemy[1]+=dy/steps
        distance=math.dist(start,enemy[:2])
        if distance>1e-8:
            if not hasattr(self,'_enemy_motion'): self._enemy_motion={}
            previous=self._enemy_motion.get(id(enemy),(0,0))
            self._enemy_motion[id(enemy)]=(previous[0]+distance,self.now)

    def unstuck_enemy(self,enemy):
        if self.enemy_position_clear(*enemy[:2]): return
        # Resolve newly raised platforms and pre-existing overlaps to nearest free cell.
        x,y=enemy[:2]; cells=[]
        for cy in range(max(1,math.floor(y)-3),min(27,math.floor(y)+4)):
            for cx in range(max(1,math.floor(x)-3),min(27,math.floor(x)+4)):
                if self.enemy_position_clear(cx+.5,cy+.5): cells.append((cx+.5,cy+.5))
        if cells:
            enemy[0],enemy[1]=min(cells,key=lambda p:(p[0]-x)**2+(p[1]-y)**2)
            self.combat.boss_pattern.pop(id(enemy),None)

    def enemy_waypoint(self,enemy,target):
        # Test body clearance along the route, rather than a zero-width ray.
        distance=math.dist(enemy[:2],target)
        steps=max(1,math.ceil(distance/.15))
        if all(self.enemy_position_clear(enemy[0]+(target[0]-enemy[0])*i/steps,enemy[1]+(target[1]-enemy[1])*i/steps) for i in range(1,steps+1)): return target
        # Shared reverse flood field: all enemies reuse the same route map.
        goal=(math.floor(target[0]),math.floor(target[1]))
        signature=(goal,frozenset(self.terrain_cells))
        if getattr(self,'_nav_signature',None)!=signature:
            self._nav_signature=signature; self._nav_field={goal:0}; queue=deque([goal])
            while queue:
                x,y=queue.popleft()
                for cell in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                    if cell not in self._nav_field and self.enemy_position_clear(cell[0]+.5,cell[1]+.5):
                        self._nav_field[cell]=self._nav_field[(x,y)]+1; queue.append(cell)
        x,y=math.floor(enemy[0]),math.floor(enemy[1])
        def reachable(cell):
            endpoint=(cell[0]+.5,cell[1]+.5)
            steps=max(1,math.ceil(math.dist(enemy[:2],endpoint)/.08))
            return all(self.enemy_position_clear(enemy[0]+(endpoint[0]-enemy[0])*i/steps,
                                                enemy[1]+(endpoint[1]-enemy[1])*i/steps)
                       for i in range(1,steps+1))
        current=self._nav_field.get((x,y),float('inf'))
        candidates=[c for c in ((x+1,y),(x-1,y),(x,y+1),(x,y-1))
                    if self._nav_field.get(c,float('inf'))<current and reachable(c)]
        # Recenter within the current cell before attempting a turn around
        # a corner. Otherwise axis collision produces sideways wall sliding.
        if not candidates and (x,y) in self._nav_field and reachable((x,y)):
            return x+.5,y+.5
        if not candidates: return enemy[:2]
        cell=min(candidates,key=lambda c:self._nav_field[c])
        return cell[0]+.5,cell[1]+.5

    def boss_intro_duration(self):
        name=('colossus','hunter','judge','weaver','executioner')[(self.pending_boss_wave//5-1)%5]
        return 15000 if all(f'fx_story_{name}_{i}' in self.cloud_art.images for i in range(6)) else 3600

    def draw_boss_intro(self):
        from rogue_content import BOSS_DESIGNS
        index=(self.pending_boss_wave//5-1)%5
        name=('colossus','hunter','judge','weaver','executioner')[index]
        elapsed=max(0,pygame.time.get_ticks()-self.boss_intro_start)
        frame=min(5,elapsed//2500)
        story=f'fx_story_{name}_{frame}'
        if story in self.cloud_art.images:
            self.screen.fill((5,6,12))
            self.cloud_art.blit(self.screen,story,(0,25,W,480))
            captions=('踏入寂静的战场','异常信号出现','裂隙开启','强敌降临','正面对峙','准备迎战')
            title=self.big_font.render(f'第 {self.pending_boss_wave} 波 · {BOSS_DESIGNS[index]["name"]}',True,(245,190,130))
            hint=self.font.render(captions[frame],True,(200,215,230))
            self.screen.blit(title,(W//2-title.get_width()//2,510))
            self.screen.blit(hint,(W//2-hint.get_width()//2,555))
            skip=self.font.render('空格 / 回车跳过',True,(150,165,185))
            self.screen.blit(skip,(W-skip.get_width()-16,H-24))
            return
        progress=min(1,(pygame.time.get_ticks()-self.boss_intro_start)/3600)
        self.screen.fill((5,6,12))
        entrance='fx_entrance_'+name+'_'+str(min(7,int(progress*8)))
        if entrance in self.cloud_art.images:
            self.cloud_art.blit(self.screen,entrance,(0,25,W,H-100))
            pygame.draw.rect(self.screen,(0,0,0),(0,H-90,W,90))
            title=self.big_font.render(BOSS_DESIGNS[index]['name'],True,(245,190,130))
            self.screen.blit(title,(W//2-title.get_width()//2,H-80))
            hint=self.font.render('强敌降临 · 演出结束后进入首领波次',True,(190,195,210))
            self.screen.blit(hint,(W//2-hint.get_width()//2,H-38))
            return
        pose='idle' if progress<.4 else 'attack_ready' if progress<.8 else 'attack_swing'
        image=self.enemy_art.cloud.get('boss_cast_'+name+'_'+pose)
        anime='anime_boss_'+name+'_motion_'+str(min(11,int(progress*12)))
        image=self.enemy_art.cloud.get(anime,image)
        effect='fx_anime_intro_'+str(min(7,int(progress*8)))
        self.cloud_art.blit(self.screen,effect,(W//2-290,H//2-290,580,580))
        if image:
            size=int(470+progress*90)
            image=pygame.transform.smoothscale(image,(size,size))
            self.screen.blit(image,image.get_rect(center=(W//2,H//2-20)))
        pygame.draw.rect(self.screen,(0,0,0),(0,0,W,55))
        pygame.draw.rect(self.screen,(0,0,0),(0,H-110,W,110))
        title=self.big_font.render(BOSS_DESIGNS[index]['name'],True,(245,190,130))
        self.screen.blit(title,(W//2-title.get_width()//2,H-100))
        hint=self.font.render('强敌降临 · 演出结束后进入首领波次',True,(190,195,210))
        self.screen.blit(hint,(W//2-hint.get_width()//2,H-53))

    def draw(self):
        if self.state=='boss_intro':
            self.screen.set_clip(None)
            self.draw_boss_intro()
            pygame.display.flip()
            return
        font=self.font
        s=self.screen; horizon=int(H/2+self.pitch*H*.72); horizon=max(90,min(H-90,horizon))
        # Cache the static sky/ground gradient by horizon. This removes ~600
        # line draw calls from every frame while pitch is unchanged.
        if horizon not in self._background_cache:
            bg=pygame.Surface((W,H));
            for y in range(horizon):
                t=y/max(1,horizon); pygame.draw.line(bg,(int(28+32*t),int(45+28*t),int(82+35*t)),(0,y),(W,y))
            for y in range(horizon,H):
                t=(y-horizon)/max(1,H-horizon); pygame.draw.line(bg,(int(48-18*t),int(52-16*t),int(58-14*t)),(0,y),(W,y))
            if len(self._background_cache)>8: self._background_cache.pop(next(iter(self._background_cache)))
            self._background_cache[horizon]=bg
        s.blit(self._background_cache[horizon],(0,0))
        # World effects must never cover the boss header or the lower HUD.
        s.set_clip(None)
        for tx,ty in ():
            corners=[self.project(tx+ox,ty+oy,z) for z in (0,self.wall_height) for ox,oy in ((0,0),(1,0),(1,1),(0,1))]
            point=self.project(tx+.5,ty+.5,0)
            if point:
                size=max(8,int(90/max(.5,math.hypot(tx+.5-self.player[0],ty+.5-self.player[1]))))
                pygame.draw.rect(s,(70,82,95),(point[0]-size,point[1]-size*2,size*2,size*2),border_radius=4)
                pygame.draw.rect(s,(110,135,150),(point[0]-size,point[1]-size*2,size*2,size*2),2,border_radius=4)
        # Lava pools are visibly hazardous and provide navigation pressure.
        for tx,ty in ():
            point=self.project(tx+.5,ty+.5,-.02)
            if point:
                size=max(6,int(70/max(.5,math.hypot(tx+.5-self.player[0],ty+.5-self.player[1]))))
                pygame.draw.rect(s,(125,35,18),(point[0]-size,point[1]-size//2,size*2,size),border_radius=3)
                pygame.draw.rect(s,(245,95,20),(point[0]-size,point[1]-size//2,size*2,size),2,border_radius=3)
        pet_point=None
        if pet_point and self.pet.get('type')!='none' and self.pet['hp']>0:
            pcol={'healer':(90,230,140),'taunter':(230,170,70),'gunner':(80,180,240),'minelayer':(190,100,220),'berserker':(230,70,80)}.get(self.pet.get('type'),(90,220,210))
            pygame.draw.circle(s,pcol,pet_point,16); pygame.draw.circle(s,(240,250,255),pet_point,6)
            # companion health bar and type label
            ratio=max(0,self.pet.get('hp',0))/max(1,self.pet.get('max_hp',1)); pygame.draw.rect(s,(50,20,20),(pet_point[0]-18,pet_point[1]-25,36,4)); pygame.draw.rect(s,(80,220,110),(pet_point[0]-18,pet_point[1]-25,int(36*ratio),4))
            tag=self.font.render(self.pet.get('type','gunner').upper(),True,pcol); s.blit(tag,(pet_point[0]-tag.get_width()//2,pet_point[1]+18))
        for mx,my,expiry in self.pet.get('mines',[]):
            point=self.project(mx,my,-.3)
            if point: pygame.draw.circle(s,(180,80,245),point,8,2)
        self.map_art.draw_space(self)
        # Terrain silhouettes are removed: outside the arena is open space.
        for layer,color in ():
            points=[(-80,horizon)]
            for i in range(15):
                px=i*90-100-int(self.angle*35)%90
                py=horizon-30-layer*12-int(18+30*math.sin(i*1.7+layer)**2)
                points.append((px,py))
            points.extend([(W+100,horizon),(W+100,horizon+5),(-80,horizon+5)])
            pygame.draw.polygon(s,color,points)
        # World-space ground grid makes movement and distance visible.
        for gx in ():
            points=[]
            for gy in range(1,28):
                point=self.project(gx,gy,-.5)
                if point and -W<point[0]<W*2 and horizon<point[1]<H*2: points.append(point)
                elif len(points)>1: pygame.draw.lines(s,THEME['grid'],False,points); points=[]
            if len(points)>1: pygame.draw.lines(s,THEME['grid'],False,points)
        for gy in ():
            points=[]
            for gx in range(1,28):
                point=self.project(gx,gy,-.5)
                if point and -W<point[0]<W*2 and horizon<point[1]<H*2: points.append(point)
                elif len(points)>1: pygame.draw.lines(s,THEME['grid'],False,points); points=[]
            if len(points)>1: pygame.draw.lines(s,THEME['grid'],False,points)
        # Ground is the background plane: render it before opaque wall faces.
        self.map_art.draw_ground(self)
        rays=W//2; colw=W/rays
        zoom=2.5 if self.ads and self.weapon_index==3 else 1.4 if self.ads else 1
        view_fov=2*math.atan(math.tan(FOV/2)/zoom)
        for i in range(rays):
            ra=self.angle+math.atan((2*(i+.5)/rays-1)*math.tan(view_fov/2))
            d,cellx,celly=ray_wall_distance(*self.player,math.cos(ra),math.sin(ra))
            d*=math.cos(ra-self.angle); projection=H*.55*zoom/max(.05,d)
            h=projection*2; shade=max(25, int(210/(1+d*.18)))
            # subtle material variation based on hit cell, avoiding obvious striping
            tint=1.0 + (((cellx*7+celly*13)%5)-2)*0.025
            # Same ground elevation (-.5) and camera height as floor projection.
            top=int(horizon+(self.z+.5-2)*projection); x=int(i*colw); width=1; c=(int(shade*tint),int(shade*tint*.96),int(shade*tint*.90))
            pygame.draw.rect(s,c,(x,top,width,int(h))); pygame.draw.line(s,(min(255,c[0]+30),min(255,c[1]+30),min(255,c[2]+30)),(x,top),(x+width,top))
            texture=self.map_art.images['wall']
            raw_depth=d/max(.01,math.cos(ra-self.angle))
            hitx=self.player[0]+math.cos(ra)*raw_depth; hity=self.player[1]+math.sin(ra)*raw_depth
            coordinate=hity if abs(hitx-round(hitx))<.01 else hitx
            column=texture.subsurface((int(coordinate*texture.get_width())%texture.get_width(),0,1,texture.get_height()))
            bottom=top+max(1,int(h)); start=max(0,top); end=min(H,bottom)
            if end>start:
                v0=max(0,min(texture.get_height()-1,int((start-top)/h*texture.get_height())))
                v1=max(v0+1,min(texture.get_height(),math.ceil((end-top)/h*texture.get_height())))
                s.blit(pygame.transform.scale(column.subsurface((0,v0,1,v1-v0)),(width,end-start)),(x,start))
        self.map_art.draw_obstacles(self)
        # Decorative billboards stay outside navigable arena; they do not imply collision.
        for px,py,name in ((.5,8.,'tree'),(.5,20.,'crystal'),(27.5,10.,'reactor'),(27.5,22.,'portal')):
            point=self.project(px,py,-.5)
            if point:
                distance=max(1,math.hypot(px-self.player[0],py-self.player[1]))
                size=max(12,min(160,int(350/distance)))
                self.cloud_art.blit(s,'prop_'+name,(point[0]-size//2,point[1]-size,size,size))
        if self.pet.get('type')!='none' and self.pet['hp']>0:
            # Every companion has a grounded collision foot; skill frames may
            # animate above it but must not make the pet float in the arena.
            point=self.project(self.pet['x'],self.pet['y'],-.5)
            if point:
                distance=max(.5,math.hypot(self.pet['x']-self.player[0],self.pet['y']-self.player[1]))
                size=min(130,max(24,int(90/distance)))
                if self.pet['type']=='taunter':
                    size=min(220,max(36,int(155/distance)))
                age=self.now-self.pet.get('animation_start',-10000)
                # Idle companions use a stable grounded frame. Only the
                # explicitly triggered skill animates, preventing the old
                # four-frame loop from looking like in-place spinning.
                frame=4+min(3,int(age/100)) if 0<=age<400 else 0
                if self.pet['type']=='taunter' and 0<=age<720: frame=4+int(age//180)%4
                pet_rect=pygame.Rect(point[0]-size//2,point[1]-size,size,size)
                boss_visuals=[self.enemy_visual(e,hit_test=True) for e in self.enemies if e[5]=='boss' and e[2]>0]
                if not any(v and pet_rect.colliderect(v[1]) for v in boss_visuals):
                    self.cloud_art.blit(s,'pet_'+self.pet['type']+'_motion_'+str(frame),pet_rect)
        station=self.project(*self.ammo_station,-.15)
        if station:
            distance=max(.5,math.hypot(self.player[0]-self.ammo_station[0],self.player[1]-self.ammo_station[1]))
            size=min(170,max(12,int(220/distance))); x,y=station
            s.blit(pygame.transform.scale(self.map_art.images['station'],(size,size)),(x-size//2,y-size//2))
            label=self.font.render('弹药补给',True,(120,255,190)); s.blit(label,(x-label.get_width()//2,y-size//2-30))
        self.corpses=[c for c in self.corpses if c[1]>self.now]
        for corpse,end in self.corpses:
            dead_enemy=corpse
            # A dead female/elite sprite can sit underneath a large boss and
            # read as a duplicate attack silhouette. Hide corpse decals while
            # a living boss occupies the same projected space.
            if any(e[5]=='boss' and e[2]>0 and math.hypot(e[0]-dead_enemy[0],e[1]-dead_enemy[1])<1.8 for e in self.enemies):
                continue
            dx,dy=dead_enemy[0]-self.player[0],dead_enemy[1]-self.player[1]
            depth=dx*math.cos(self.angle)+dy*math.sin(self.angle)
            point=self.project(dead_enemy[0],dead_enemy[1],0)
            if depth>.12 and point and self.world_los(*self.player,dead_enemy[0],dead_enemy[1]):
                dead_visual=self.enemy_visual(dead_enemy,state='dead')
                if dead_visual:
                    image,rect=dead_visual
                    # Compare screen footprints: perspective can overlap a
                    # distant corpse and boss despite large world separation.
                    boss_rects=[self.enemy_visual(e,hit_test=True) for e in self.enemies if e[5]=='boss' and e[2]>0]
                    if any(visual and rect.colliderect(visual[1]) for visual in boss_rects): continue
                    s.blit(image,rect)
                else:
                    radius=max(3,min(40,int(35/depth)))
                    pygame.draw.ellipse(s,(65,45,45),(point[0]-radius,point[1],radius*2,max(3,radius//2)))
        # Drawing and hit detection share enemy_visual; health bars are not hittable.
        for enemy in sorted(self.enemies,key=lambda e:math.hypot(e[0]-self.player[0],e[1]-self.player[1]),reverse=True):
            visual=self.enemy_visual(enemy)
            if visual and line_of_sight(*self.player,enemy[0],enemy[1]):
                image,rect=visual
                ground_point=self.project(enemy[0],enemy[1],-.5)
                if ground_point:
                    shadow_width=max(6,image.get_bounding_rect(min_alpha=128).width*2//3)
                    shadow_height=max(3,min(12,shadow_width//6))
                    # Use a subtle contact shadow so the generated character
                    # does not appear to have a gray outline under its feet.
                    shadow=pygame.Surface((shadow_width,shadow_height),pygame.SRCALPHA)
                    pygame.draw.ellipse(shadow,(8,12,16,85),(0,0,shadow_width,shadow_height))
                    s.blit(shadow,(ground_point[0]-shadow_width//2,ground_point[1]-shadow_height//2))
                s.blit(image,rect)
                bounds=image.get_bounding_rect(min_alpha=128)
                width=max(24,bounds.width); bar=pygame.Rect(rect.x+bounds.centerx-width//2,rect.y+bounds.y-12,width,5)
                pygame.draw.rect(s,(45,20,25),bar)
                pygame.draw.rect(s,(90,230,125),(bar.x,bar.y,int(width*max(0,enemy[2])/enemy[4]),5))
        self.damage_popups=[p for p in self.damage_popups if p['end']>self.now]
        for popup in self.damage_popups:
            enemy=popup['target']
            if not self.world_los(*self.player,*enemy[:2]): continue
            point=self.project(*enemy[:2],.65 if enemy[5]!='bat' else 1.1)
            if point:
                age=(self.now-popup['start'])/850
                label=self.font.render(f'-{popup["amount"]:.0f}',True,(255,213,90))
                label.set_alpha(max(0,min(255,int((popup['end']-self.now)/250*255))))
                s.blit(label,(point[0]-label.get_width()//2,point[1]-int(age*40)))
        for p in self.projectiles:
            bullet_z=p[6] if len(p)>6 else 0.
            point=self.project(p[0],p[1],bullet_z)
            tail=self.project(p[0]-p[2]*.12,p[1]-p[3]*.12,bullet_z)
            dist=math.hypot(p[0]-self.player[0],p[1]-self.player[1])
            radius=max(5,min(65,int(35/max(.35,dist))))
            if point:
                projectile_kind=p[8] if len(p)>8 else ''
                if projectile_kind.startswith('boss_'):
                    key='fx_boss_ammo_'+projectile_kind[5:]
                    size=int(radius*{'boss_colossus':3.2,'boss_hunter':2.,'boss_judge':1.8,'boss_weaver':2.8,'boss_executioner':3.}[projectile_kind])
                    if self.cloud_art.blit(s,key,(point[0]-size//2,point[1]-size//2,size,size)): continue
                if tail:
                    tx,ty=tail; px,py=point; length=math.hypot(tx-px,ty-py)
                    if length>100: tx=px+(tx-px)*100/length; ty=py+(ty-py)*100/length
                    pygame.draw.line(s,(255,80,50),(int(tx),int(ty)),point,max(2,min(6,radius//3)))
                glow=pygame.Surface((radius*4,radius*4),pygame.SRCALPHA)
                pygame.draw.circle(glow,(255,75,30,35),(radius*2,radius*2),radius*2)
                pygame.draw.circle(glow,(255,160,40,125),(radius*2,radius*2),radius)
                pygame.draw.circle(glow,(255,250,190,235),(radius*2,radius*2),max(3,radius//3))
                s.blit(glow,(point[0]-radius*2,point[1]-radius*2))
                key='fx_wave' if len(p)>8 and p[8]=='wave' else 'fx_bullet'
                self.cloud_art.blit(s,key,(point[0]-radius,point[1]-radius,radius*2,radius*2))
            if dist<2:
                dx,dy=p[0]-self.player[0],p[1]-self.player[1]
                angle=math.atan2(dy,dx)-self.angle
                cx=int(W/2+math.sin(angle)*(W/2-40)); cy=int(H/2-math.cos(angle)*(H/2-145))
                pygame.draw.circle(s,(255,100,45),(cx,cy),18,4)
        for x,y,angle,pitch,distance,start,end in ():
            travel=min(distance,(self.now-start)*.12+1)
            point=self.project(x+math.cos(angle)*travel,y+math.sin(angle)*travel,pitch*travel*(.72/.55))
            if point:
                pygame.draw.line(s,(255,210,100),(W//2,H-105),point,2)
                pygame.draw.circle(s,(255,245,185),point,3)
        # End world-only clipping before first-person weapon and HUD.
        s.set_clip(None)
        # Procedural first-person weapon and gloved hands.
        progress=(self.now-getattr(self,'reload_start',self.now))/self.reload_duration if self.reload_until else 0
        recoil=max(0,(self.muzzle_until-self.now)/70)*12
        gun_y=H-28+int(recoil)+int(math.sin(self.walk_phase)*3)+int(math.sin(min(1,progress)*math.pi)*45)
        center=W//2
        kind=WEAPONS[self.weapon_index].get('kind','gun')
        if kind not in ('melee','shield') and 'weapon_smg' not in self.cloud_art.images:
            pygame.draw.polygon(s,(45,55,64),[(center-150,H),(center-88,gun_y-90),(center-35,gun_y-52),(center-15,H)])
            pygame.draw.polygon(s,(35,43,52),[(center+155,H),(center+95,gun_y-80),(center+35,gun_y-46),(center+25,H)])
            pygame.draw.ellipse(s,(80,88,90),(center-90,gun_y-100,65,56))
            pygame.draw.ellipse(s,(70,77,82),(center+25,gun_y-81,65,52))
            pygame.draw.polygon(s,(38,40,48),[(center-42,H),(center+42,H),(center+25,gun_y-30),(center-25,gun_y-30)])
            pygame.draw.rect(s,(75,78,88),(W//2-8,gun_y-55,16,45)); pygame.draw.rect(s,(28,30,36),(W//2-4,gun_y-75,8,24))
        weapon_color=(100,170,230) if self.weapon_level<6 else (170,100,250) if self.weapon_level<9 else (255,180,65)
        if kind not in ('melee','shield') and 'weapon_smg' not in self.cloud_art.images:
            barrels=[22,36,28,12]; length=[60,48,75,110]
            idx=min(self.weapon_index,3)
            pygame.draw.rect(s,(75,88,103),(W//2-barrels[idx]//2,gun_y-length[idx],barrels[idx],length[idx]-15),border_radius=3)
            if idx==2: pygame.draw.rect(s,(120,100,55),(W//2+18,gun_y-45,40,25))
            if idx==3: pygame.draw.ellipse(s,(35,45,60),(W//2-18,gun_y-100,36,18))
            # Receiver and highlights make all four silhouettes visibly distinct.
            idx=min(self.weapon_index,3)
            receiver_width=(64,80,100,58)[idx]
            receiver_top=gun_y-(110,95,115,150)[idx]
            if kind not in ('melee','shield'): pygame.draw.polygon(s,(43,53,63),[(center-receiver_width//2,gun_y-15),(center+receiver_width//2,gun_y-15),
                                                         (center+receiver_width//3,receiver_top),(center-receiver_width//3,receiver_top)])
            if kind not in ('melee','shield'):
                pygame.draw.line(s,(120,140,150),(center-receiver_width//3,receiver_top),(center+receiver_width//3,receiver_top),3)
                pygame.draw.rect(s,(25,31,37),(center-8,receiver_top-30,16,38),border_radius=2)
                pygame.draw.rect(s,(155,170,175),(center-3,receiver_top-28,6,7))
            if self.weapon_index==0:
                pygame.draw.rect(s,(25,32,40),(center-18,gun_y-36,36,45),border_radius=3)
                pygame.draw.rect(s,(70,95,110),(center-15,receiver_top+8,30,12),2)
            elif self.weapon_index==1:
                pygame.draw.rect(s,(115,75,45),(center-27,gun_y-66,54,31),border_radius=6)
                for offset in range(-20,25,8): pygame.draw.line(s,(55,40,30),(center+offset,gun_y-63),(center+offset,gun_y-38),2)
                pygame.draw.rect(s,(110,120,130),(center-12,receiver_top-45,24,46),border_radius=3)
            elif self.weapon_index==2:
                pygame.draw.rect(s,(110,94,45),(center+35,gun_y-60,65,55),border_radius=4)
                for offset in range(0,40,8): pygame.draw.rect(s,(205,175,70),(center+41+offset,gun_y-68,5,20))
                for offset in (-20,-10,0,10,20): pygame.draw.line(s,(20,28,33),(center+offset,receiver_top+14),(center+offset,receiver_top+34),3)
            else:
                pygame.draw.rect(s,(20,28,35),(center-16,receiver_top-25,32,65),border_radius=8)
                pygame.draw.ellipse(s,(100,200,215),(center-12,receiver_top-21,24,13))
                pygame.draw.line(s,(140,165,175),(center+25,gun_y-92),(center+50,gun_y-73),5)
                pygame.draw.circle(s,(90,100,110),(center+50,gun_y-73),7)
            if self.reload_until:
                mx=W//2+45; my=H-65+int(math.sin(progress*math.pi)*30)
                pygame.draw.rect(s,(110,120,135),(mx,my,18,45),border_radius=3)
                pygame.draw.ellipse(s,(155,115,90),(mx-15,my+25,45,25))
                pygame.draw.rect(s,(45,55,70),(W//2-90,H-130,180,8))
                pygame.draw.rect(s,(90,210,180),(W//2-90,H-130,int(180*min(1,progress)),8))
            pygame.draw.rect(s,weapon_color,(W//2-18,gun_y-50,36,8))
            if self.weapon_level>=3:
                pygame.draw.rect(s,(65,75,90),(W//2-22,gun_y-65,10,45)); pygame.draw.rect(s,(65,75,90),(W//2+12,gun_y-65,10,45))
        self.cloud_art.weapon(self)
        # crosshair and HUD
        if self.ads and self.state=='playing' and self.weapon_index==3:
            mask=pygame.Surface((W,H),pygame.SRCALPHA); mask.fill((0,0,0,235))
            pygame.draw.circle(mask,(0,0,0,0),(W//2,H//2),230); s.blit(mask,(0,0))
        pygame.draw.circle(s,(245,245,245),(W//2,H//2),5,1)
        if self.hit_until>self.now:
            for sx,sy in ((-1,-1),(-1,1),(1,-1),(1,1)):
                pygame.draw.line(s,(255,215,120),(W//2+sx*9,H//2+sy*9),(W//2+sx*16,H//2+sy*16),2)
        popup=getattr(self,'kill_popup',None)
        if popup and popup[1]>self.now and self.state=='playing':
            panel=pygame.Rect(W//2-208,H-148,416,76)
            pygame.draw.rect(s,(13,22,33),panel,border_radius=12)
            pygame.draw.rect(s,(205,155,65),panel,1,border_radius=12)
            medal='icon_kill_'+str(min(7,self.kill_streak))
            self.cloud_art.blit(s,medal,(panel.x+10,panel.y+8,58,58))
            label=self.font.render(popup[0],True,(255,215,120))
            s.blit(label,(panel.x+78,panel.y+8))
            x=panel.x+78
            for method,title in (('headshot','爆头'),('melee','近战')):
                count=self.streak_methods[method]
                if count:
                    self.cloud_art.blit(s,'icon_kill_'+method,(x,panel.y+36,28,28))
                    detail=self.card_font.render(f'{title} ×{count}',True,(255,150,145) if method=='headshot' else (110,235,235))
                    s.blit(detail,(x+31,panel.y+40)); x+=145
        hud_offset=48 if any(e[5]=='boss' for e in self.enemies) else 0
        font=self.font; text=f"生命 {int(self.hp)}/{self.max_hp}  护盾 {math.ceil(self.shield)}  弹匣 {self.mag}  备弹 {self.reserve}/{self.reserve_max}  波次 {self.wave}  敌人 {len(self.enemies)}"
        text += "  RELOADING" if self.reload_until else ""
        hud_rect=pygame.Rect(10,10+hud_offset,W-20,112)
        pygame.draw.rect(s,THEME['ink2'],hud_rect,border_radius=12); pygame.draw.rect(s,THEME['panel2'],hud_rect.inflate(-6,-6),border_radius=9)
        self.cloud_art.blit(s,'hud_v2_frame',hud_rect)
        pygame.draw.rect(s,THEME['panel'],(18,18+hud_offset,W-36,88),border_radius=4)
        pygame.draw.line(s,THEME['acid'],(hud_rect.x+12,hud_rect.bottom-10),(hud_rect.x+170,hud_rect.bottom-10),4)
        s.blit(font.render(text,True,THEME['paper']),(20,18+hud_offset)); s.blit(font.render(self.message,True,THEME['acid']),(20,48+hud_offset))
        s.blit(font.render(f'等级 {self.level} · 经验 {self.xp:g}/{self.xp_needed} · 击杀 {self.kills} · ESC 暂停 / Q 退出',True,(150,200,230)),(20,78+hud_offset))
        s.blit(font.render('WASD / 方向键移动 · Space 跳跃 · Shift 冲刺 · M 音效开关',True,(190,210,220)),(20,H-28))
        s.blit(font.render(f'{self.weapon_name()} Lv.{self.weapon_level}',True,weapon_color),(W-290,H-60))
        if self.ads and self.state=='playing':
            pygame.draw.circle(s,(100,230,210),(W//2,H//2),80,2)
            pygame.draw.line(s,(80,160,145),(W//2-100,H//2),(W//2+100,H//2),1)
            pygame.draw.line(s,(80,160,145),(W//2,H//2-100),(W//2,H//2+100),1)
        bosses=[e for e in self.enemies if e[5]=='boss']
        if bosses:
            boss=bosses[0]
            from rogue_content import BOSS_DESIGNS
            boss_name=BOSS_DESIGNS[(self.wave//5-1)%5]['name']
            phase='狂暴' if boss[2]<=boss[4]*.5 else '第一阶段'
            title=font.render(f'{boss_name} · {phase}',True,(255,170,190))
            health=font.render(f'{math.ceil(max(0,boss[2]))} / {math.ceil(boss[4])}',True,(255,210,215))
            panel_width=min(W-40,max(660,title.get_width()+56,health.get_width()+56))
            panel=pygame.Rect((W-panel_width)//2,4,panel_width,86)
            pygame.draw.rect(s,(15,20,30),panel,border_radius=6)
            self.cloud_art.blit(s,'boss_frame',panel)
            if title.get_width()>panel.width-40:
                title=pygame.transform.smoothscale(title,(panel.width-40,title.get_height()))
            if health.get_width()>panel.width-40:
                health=pygame.transform.smoothscale(health,(panel.width-40,health.get_height()))
            s.blit(title,(panel.centerx-title.get_width()//2,panel.y+8))
            s.blit(health,(panel.centerx-health.get_width()//2,panel.y+34))
            bar=pygame.Rect(panel.x+20,panel.bottom-18,panel.width-40,9)
            pygame.draw.rect(s,(65,25,40),bar,border_radius=3)
            filled=bar.copy(); filled.width=round(bar.width*max(0,min(1,boss[2]/max(1,boss[4]))))
            pygame.draw.rect(s,(245,70,100),filled,border_radius=3)
        pygame.draw.rect(s,(35,45,60),(20,109+hud_offset,W-40,5)); pygame.draw.rect(s,(70,210,200),(20,109+hud_offset,int((W-40)*min(1,self.xp/self.xp_needed)),5))
        if self.damage_until>self.now:
            pygame.draw.rect(s,(210,45,40),(0,0,W,H),12)
        if self.wave_wait and self.state=='playing':
            s.blit(font.render(f'下一波准备中：{max(0,math.ceil((self.wave_wait-self.now)/1000))} 秒',True,(130,240,200)),(20,H-40))
        if self.state == 'upgrade':
            overlay=pygame.Surface((W,H),pygame.SRCALPHA); overlay.fill((5,8,18,225)); s.blit(overlay,(0,0))
            s.blit(self.big_font.render('Boss 战利品' if self.reward_is_boss else '升级！选择一项强化',True,(255,220,110)),(260,155))
            for i,(key,title,description,rank,scale) in enumerate(self.choices):
                rect=pygame.Rect(35+i*305,245,285,210)
                pygame.draw.rect(s,THEME['ink2'],rect,border_radius=12); pygame.draw.rect(s,THEME['panel'],rect.inflate(-6,-6),border_radius=9)
                pygame.draw.circle(s,THEME['violet'],(rect.right-22,rect.top+22),7)
                self.cloud_art.blit(s,'card_v2_frame',rect)
                pygame.draw.rect(s,TIERS[rank][1],rect,4,border_radius=12)
                self.draw_icon(key,(rect.centerx,rect.y+48))
                title_text=f'{i+1}  {title}'
                title_image=self.card_font.render(title_text,True,(255,230,130))
                if title_image.get_width()>rect.width-30:
                    title_image=pygame.transform.smoothscale(title_image,(rect.width-30,title_image.get_height()))
                s.blit(title_image,(rect.x+15,rect.y+85))
                lines=[]; current=''
                for char in description:
                    if current and self.card_font.size(current+char)[0]>rect.width-30:
                        lines.append(current); current=char
                    else: current+=char
                if current: lines.append(current)
                for row,line in enumerate(lines[:3]):
                    if row==2 and len(lines)>3: line=line[:-1]+'…'
                    s.blit(self.card_font.render(line,True,(230,235,240)),(rect.x+15,rect.y+115+row*21))
                s.blit(self.card_font.render(f'强度 ×{scale:g} · 已选 {self.upgrade_stacks.get(key,0)}',True,TIERS[rank][1]),(rect.x+15,rect.y+184))
            s.blit(font.render('按 1 / 2 / 3 或点击卡片 · 战斗已暂停 · Q 退出',True,(215,225,240)),(210,495))
        if self.state=='wave':
            self.draw_wave_notice(s)
        if self.state=='menu':
            s.blit(self.map_art.images['menu'],(0,0))
            overlay=pygame.Surface((W,H),pygame.SRCALPHA); overlay.fill((5,10,20,235)); s.blit(overlay,(0,0))
            self.cloud_art.blit(s,'pause_v2_frame',(105,70,750,440))
            for text,y,color in [('异维实验室 · 无限强化',130,THEME['acid']),
                                 ('Enter / 点击开始 · 生存、升级、挑战每五波 Boss',215,(220,235,245)),
                                 ('WASD 移动 · 鼠标瞄准 · 左键开火 · 右键开镜',275,(180,215,235)),
                                 ('R 换弹 · F 补给 · 1–3 武器槽（最多三把）',310,(180,215,235)),
                                 ('Esc 暂停 · M 静音 · Q 退出',345,(180,215,235))]:
                label=(self.big_font if y==130 else font).render(text,True,color)
                s.blit(label,(W//2-label.get_width()//2,y))
            rect=pygame.Rect(W//2-120,415,240,55)
            pygame.draw.rect(s,THEME['acid'],rect,border_radius=10)
            pygame.draw.rect(s,THEME['ink2'],rect.inflate(-4,-4),border_radius=8)
            label=font.render('开始新一局',True,THEME['acid']); s.blit(label,(rect.centerx-label.get_width()//2,rect.y+15))
            s.blit(font.render(VERSION,True,(140,175,190)),(20,H-30))
        if self.state == "paused":
            overlay=pygame.Surface((W,H), pygame.SRCALPHA); overlay.fill((0,0,0,170)); s.blit(overlay,(0,0))
            self.cloud_art.blit(s,'pause_v2_frame',(200,180,560,240))
            s.blit(font.render("暂停",True,(255,255,255)),(W//2-45,H//2-30))
            s.blit(font.render("ESC 继续   R 新开一局   Q 退出",True,(255,255,255)),(W//2-160,H//2+5))
        elif self.state in ("won", "lost"):
            overlay=pygame.Surface((W,H), pygame.SRCALPHA); overlay.fill((0,0,0,155)); s.blit(overlay,(0,0))
            title=f"本局结束 · 波次 {self.wave} · 等级 {self.level} · 击杀 {self.kills}"
            label=font.render(title,True,(255,220,80)); s.blit(label,(W//2-label.get_width()//2,H//2-30))
            s.blit(font.render("Enter / R 新开一局   Q 退出",True,(255,255,255)),(W//2-150,H//2+5))
        if False:  # Muzzle flashes are already included in the weapon animation frames.
            center=(W//2,gun_y-(110,95,115,150)[min(self.weapon_index,3)]-30)
            points=[]
            for i in range(12):
                angle=i*math.pi/6; radius=32 if i%2==0 else 10
                points.append((center[0]+math.cos(angle)*radius,center[1]+math.sin(angle)*radius))
            pygame.draw.polygon(s,(255,165,45),points)
            pygame.draw.circle(s,(255,245,185),center,10)
        labels=' · '.join(f'{slot+1} {WEAPONS[index]["name"]}'+(' [使用中]' if index==self.weapon_index else '') for slot,index in enumerate(self.weapon_slots))
        if self.state=='playing':
            for slot,index in enumerate(self.weapon_slots):
                rect=(20+slot*66,H-135,58,48)
                pygame.draw.rect(s,(35,55,65),rect,border_radius=4)
                pygame.draw.rect(s,weapon_color if index==self.weapon_index else (90,110,125),rect,2,border_radius=4)
                s.blit(font.render(str(slot+1),True,(230,240,250)),(rect[0]+18,rect[1]+10))
                self.cloud_art.blit(s,'slot_v2_frame',rect)
                self.cloud_art.blit(s,'weapon_'+('smg','shotgun','mg','sniper','sword','boomerang','spear','dagger')[index],(rect[0]+8,rect[1]+6,36,30))
        if self.state=='playing': s.blit(font.render(labels,True,(175,200,220)),(20,H-55))
        # Dedicated melee animation/UI layer, independent of gun geometry.
        if self.state=='playing': self.combat.draw(s)
        if self.state=='playing' and WEAPONS[self.weapon_index].get('kind') in ('melee','shield'):
            if 'weapon_sword' not in self.cloud_art.images: self.combat.draw_weapon(s,(W//2, H-125),H-80)
            mode='防御中' if self.guarding else ('右键防御 · 左键攻击' if self.weapon_index==4 else '左键投掷' if self.weapon_index in (5,6) else '左键闪现攻击')
            pygame.draw.rect(s,(18,25,38),(W//2-155,H-105,310,30),border_radius=8)
            s.blit(font.render(f'{WEAPONS[self.weapon_index]["name"]}  ·  {mode}',True,(230,240,255)),(W//2-140,H-99))
        if self.state=='playing' and self.near_ammo_station():
            prompt=font.render('备弹已满' if self.reserve>=self.reserve_max else '按 F 补充备弹',True,(130,255,185))
            s.blit(prompt,(W//2-prompt.get_width()//2,H//2+105))
        elif self.state=='playing' and self.reserve<self.mag_size:
            dx,dy=self.ammo_station[0]-self.player[0],self.ammo_station[1]-self.player[1]
            direction=(math.atan2(dy,dx)-self.angle+math.pi)%(2*math.pi)-math.pi
            arrow_x=max(40,min(W-40,int(W//2+direction/math.pi*(W//2-40))))
            pygame.draw.polygon(s,(100,240,170),[(arrow_x-8,H-95),(arrow_x+8,H-95),(arrow_x,H-107)])
            label=font.render(f'补给 {math.hypot(dx,dy):.0f} m',True,(130,240,185))
            s.blit(label,(max(5,min(W-label.get_width()-5,arrow_x-label.get_width()//2)),H-90))
        if self.state=='playing' and self.pet.get('type')!='none':
            names={'healer':'治疗精灵','taunter':'诱饵守卫','gunner':'机枪无人机','minelayer':'布雷巡逻犬','berserker':'狂暴精灵'}
            typ=self.pet['type']; x,y=W-245,110
            pygame.draw.rect(s,(18,27,40),(x,y,230,83),border_radius=8)
            pygame.draw.circle(s,(100,205,220),(x+24,y+24),16,2)
            glyph={'healer':'+','taunter':'T','gunner':'G','minelayer':'M','berserker':'!'}[typ]
            s.blit(self.font.render(glyph,True,(220,245,250)),(x+17,y+10))
            s.blit(self.font.render(f'{names[typ]} Lv.{self.pet["level"]}',True,(220,240,250)),(x+46,y+8))
            status=f'复活 {self.pet["revive"]:.1f}秒' if self.pet['hp']<=0 else f'生命 {int(self.pet["hp"])}/{int(self.pet["max_hp"])}'
            s.blit(self.font.render(status,True,(120,225,155)),(x+10,y+36))
            cd=max(self.pet_cooldown,self.pet_skill_cooldown)/1000
            s.blit(self.font.render(f'技能冷却 {cd:.1f}秒',True,(155,180,210)),(x+10,y+59))
        if self.state=='character':
            overlay=pygame.Surface((W,H),pygame.SRCALPHA); overlay.fill((8,14,24,245)); s.blit(overlay,(0,0))
            pygame.draw.rect(s,THEME['portal'],(45,45,W-90,H-90),2,border_radius=12)
            self.cloud_art.blit(s,'player_portrait',(65,120,320,360))
            lines=[('维度行者 · 角色档案',THEME['acid']),
                   (f'伤害 {self.damage:.1f} · 攻击间隔 {self.fire_delay:.0f}ms',THEME['paper']),
                   (f'移速 {self.move_speed:.2f} · 减伤 {min(.7,self.extras.get("armor",0)):.0%}',THEME['paper']),
                   (f'生命 {int(self.hp)}/{self.max_hp}   护盾 {math.ceil(self.shield)}',THEME['portal']),
                   (f'等级 {self.level}   波次 {self.wave}   击杀 {self.kills}',THEME['paper']),
                   (f'当前武器：{self.weapon_name()}',THEME['paper']),
                   (f'弹匣 {self.mag}/{self.mag_size} · 备弹 {self.reserve}',THEME['paper']),
                   ('Tab / ESC 返回',THEME['acid'])]
            for row,(label,color) in enumerate(lines):
                s.blit(font.render(label,True,color),(405,105+row*45))
        elif self.state in ('menu','paused','playing'):
            s.blit(self.card_font.render('Tab 角色属性',True,THEME['acid']),(W-145,H-28))
        pygame.display.flip()

    def weapon_name(self):
        return WEAPONS[self.weapon_index]['name']

    def draw_wave_notice(self,surface):
        remaining=max(0,self.wave_deadline-pygame.time.get_ticks())
        # The preparation period is 3 seconds. Ease in/out instead of
        # covering the arena with an opaque, oversized announcement.
        elapsed=max(0,3000-remaining)
        opacity=max(0,min(1,elapsed/280,remaining/380))
        panel=pygame.Surface((420,106),pygame.SRCALPHA)
        accent=(181,153,209) if self.wave%5==0 else (104,195,184)
        pygame.draw.rect(panel,(15,26,36,215),(0,0,420,106),border_radius=12)
        pygame.draw.rect(panel,(*accent,95),(0,0,420,106),1,border_radius=12)
        pygame.draw.line(panel,(*accent,180),(22,22),(22,67),3)
        title=self.font.render(f'第 {self.wave:02d} 波'+(' · 首领挑战' if self.wave%5==0 else ' · 准备迎战'),True,(218,233,235))
        panel.blit(title,(38,18))
        hint=self.card_font.render(f'{math.ceil(remaining/1000)} 秒后开始  ·  可移动与切换武器',True,(149,176,185))
        panel.blit(hint,(38,51))
        pygame.draw.rect(panel,(46,65,75),(22,87,376,3),border_radius=1)
        pygame.draw.rect(panel,accent,(22,87,round(376*min(1,elapsed/3000)),3),border_radius=1)
        panel.set_alpha(round(255*opacity))
        surface.blit(panel,((W-420)//2,150+round(8*(1-opacity))))

    def draw_icon(self,key,center):
        if self.cloud_art.blit(self.screen,'icon_'+key,(center[0]-28,center[1]-28,56,56)): return
        x,y=center; s=self.screen; color=(100,230,210)
        pygame.draw.circle(s,(15,30,45),center,30)
        if key in ('health','regen','leech','heal'):
            pygame.draw.rect(s,(240,100,130) if key=='leech' else color,(x-5,y-19,10,38))
            pygame.draw.rect(s,(240,100,130) if key=='leech' else color,(x-19,y-5,38,10))
        elif key in ('power','pierce','magazine','smg_mag','blue_supply','shot_power','mg_power','sniper_power') or key.startswith('unlock'):
            magazine=key in ('magazine','smg_mag','blue_supply')
            for i in range(3 if magazine else 1):
                ox=x-8+(i-1)*13 if magazine else x-8
                pygame.draw.rect(s,color,(ox,y-9,12,28))
                pygame.draw.polygon(s,(255,220,120),[(ox,y-9),(ox+6,y-22),(ox+12,y-9)])
            if key.startswith('unlock'): pygame.draw.circle(s,(255,220,100),center,25,2)
        elif key=='blast':
            pygame.draw.circle(s,(255,170,80),center,12)
            for a in range(0,360,45):
                r=math.radians(a); pygame.draw.line(s,(255,200,100),(x+math.cos(r)*18,y+math.sin(r)*18),(x+math.cos(r)*26,y+math.sin(r)*26),3)
        elif key in ('reload','mg_reload','orange_reset'):
            pygame.draw.arc(s,color,(x-20,y-20,40,40),.3,5.6,4)
            pygame.draw.polygon(s,color,[(x+20,y-17),(x+12,y-20),(x+20,y-7)])
        elif key in ('armor','shield','dodge'):
            pygame.draw.polygon(s,color,[(x-20,y-19),(x+20,y-19),(x+17,y+10),(x,y+25),(x-17,y+10)],3)
            pygame.draw.line(s,color,(x,y-14),(x,y+13),3)
        elif key in ('crit','critpower','range','shot_tight'):
            pygame.draw.circle(s,color,center,18,3)
            pygame.draw.circle(s,(255,215,100),center,4)
            pygame.draw.line(s,color,(x-26,y),(x+26,y),2); pygame.draw.line(s,color,(x,y-26),(x,y+26),2)
        elif key in ('burn','poison'):
            pygame.draw.polygon(s,(255,140,70) if key=='burn' else (110,235,125),[(x,y-25),(x-18,y+5),(x-13,y+20),(x+13,y+20),(x+18,y+5)])
            pygame.draw.circle(s,(245,250,190),(x,y+10),6)
        elif key=='slow':
            for a in range(0,180,60):
                r=math.radians(a); pygame.draw.line(s,(130,220,255),(x-math.cos(r)*24,y-math.sin(r)*24),(x+math.cos(r)*24,y+math.sin(r)*24),3)
        elif key=='pellets':
            for ox,oy in ((0,-15),(-15,12),(15,12)): pygame.draw.circle(s,(255,205,105),(x+ox,y+oy),7)
        elif key=='xp':
            pygame.draw.rect(s,color,(x-21,y-17,42,34),3,border_radius=3)
            pygame.draw.line(s,color,(x,y-17),(x,y+17),3)
        elif key in ('speed','haste','smg_haste','sniper_haste','knockback'):
            for ox in (-11,8): pygame.draw.lines(s,color,False,[(x+ox-8,y-20),(x+ox+9,y),(x+ox-8,y+20)],5)
        elif key=='execute':
            pygame.draw.circle(s,(230,235,240),(x,y-5),19)
            pygame.draw.circle(s,(20,30,40),(x-7,y-7),5); pygame.draw.circle(s,(20,30,40),(x+7,y-7),5)
            pygame.draw.rect(s,(230,235,240),(x-10,y+10,20,12))
        else:
            pygame.draw.polygon(s,color,[(x+5,y-24),(x-16,y+2),(x-2,y+2),(x-5,y+24),(x+18,y-4),(x+3,y-4)])

    def enemy_visual(self,e,hit_test=False,state=None):
        dx,dy=e[0]-self.player[0],e[1]-self.player[1]
        depth=dx*math.cos(self.angle)+dy*math.sin(self.angle)
        if depth<=.12: return None
        side=-dx*math.sin(self.angle)+dy*math.cos(self.angle)
        zoom=2.5 if self.ads and self.weapon_index==3 else 1.4 if self.ads else 1
        focal=W/(2*math.tan(FOV/2))*zoom; sx=int(W/2+side/depth*focal)
        size=min(650,max(10,int(H/(depth+.1)*.55*zoom)))
        visual=self.enemy_art.visual(self,e,sx,size,state=state)
        animation=self.attack_animations.get(id(e))
        if visual and not hit_test and animation and animation[1]>self.now:
            image,rect=visual
            image=image.copy()
            pygame.draw.arc(image,(255,180,65),(0,0,max(8,rect.width-1),max(8,rect.height//2)),0,math.pi,3)
            return image,rect
        return visual
        scale=1.8 if e[5]=='boss' else 1.35 if e[5] in ('elite','tank') else .8 if e[5]=='runner' else 1
        body=max(4,int(size*.23*scale)); width=body*4+8; height=size+8
        rect=pygame.Rect(sx-width//2,int(H/2+self.pitch*H*.72-size*.5+self.z/depth*H*.55*zoom),width,height)
        if rect.right<0 or rect.left>W: return None
        image=pygame.Surface((width,height),pygame.SRCALPHA); cx=width//2
        colors={'normal':(205,55,55),'runner':(230,145,50),'shooter':(50,170,230),'elite':(175,90,240),'boss':(240,65,110),'tank':(175,90,240)}
        color=(255,235,120) if e[3]>self.now else colors[e[5]]
        dark=tuple(max(15,int(v*.45)) for v in color)
        stride=int(math.sin(self.now*.007+e[0])*size*.06)
        pygame.draw.line(image,(65,75,90),(cx-body//2,int(size*.64)),(cx-body+stride,size),max(2,body//2))
        pygame.draw.line(image,(65,75,90),(cx+body//2,int(size*.64)),(cx+body-stride,size),max(2,body//2))
        pygame.draw.rect(image,color,(cx-body,int(size*.36),body*2,max(3,int(size*.31))),border_radius=max(1,body//3))
        pygame.draw.line(image,dark,(cx-body,int(size*.37)),(cx-body,int(size*.66)),max(2,body//5))
        pygame.draw.line(image,tuple(min(255,v+35) for v in color),(cx-body,int(size*.36)),(cx+body,int(size*.36)),max(1,size//50))
        pygame.draw.rect(image,(45,55,65),(cx-body//2,int(size*.4),body,max(2,int(size*.2))))
        for row in (.44,.51,.58):
            pygame.draw.line(image,(100,115,130),(cx-body//3,int(size*row)),(cx+body//3,int(size*row)),max(1,size//80))
        pygame.draw.circle(image,color,(cx,int(size*.25)),max(3,size//8))
        pygame.draw.rect(image,(20,30,40),(cx-size//10,int(size*.22),max(3,size//5),max(2,size//16)),border_radius=max(1,size//60))
        pygame.draw.line(image,(120,255,245),(cx-size//13,int(size*.25)),(cx+size//13,int(size*.25)),max(1,size//30))
        if e[5]=='shooter':
            pygame.draw.rect(image,(25,40,55),(cx+body//2,int(size*.5),max(4,body),max(3,size//18)))
            pygame.draw.circle(image,(80,205,255),(cx+body,int(size*.5)),max(2,size//45))
        elif e[5]=='runner':
            pygame.draw.line(image,(255,215,100),(cx-body,int(size*.6)),(cx-body//2,int(size*.75)),max(2,size//25))
        if e[5] in ('elite','boss','tank'):
            pygame.draw.circle(image,color,(cx-body,int(size*.4)),max(3,body//2)); pygame.draw.circle(image,color,(cx+body,int(size*.4)),max(3,body//2))
        if e[5]=='boss': pygame.draw.polygon(image,(255,210,90),[(cx-body//2,int(size*.12)),(cx-body//2,int(size*.02)),(cx,int(size*.08)),(cx+body//2,int(size*.02)),(cx+body//2,int(size*.12))])
        animation=self.attack_animations.get(id(e))
        active=animation and animation[1]>self.now
        arm_y=int(size*.42)
        raised=active and animation[0]=='melee'
        for sign in (-1,1):
            hand=(cx+sign*int(body*1.5),int(size*(.2 if raised else .55)))
            pygame.draw.line(image,color,(cx+sign*body,arm_y),hand,max(2,body//3))
        if not hit_test and active and animation[0]=='melee':
            pygame.draw.arc(image,(255,180,65),(cx-body*2,0,body*4,max(8,int(size*.5))),0,math.pi,3)
        elif not hit_test and active and animation[0]=='swing':
            pygame.draw.arc(image,(255,230,150),(cx-body*2,int(size*.25),body*4,max(8,int(size*.5))),.2,2.8,3)
        # Muzzle flashes are supplied by the weapon FX layer; never bake a
        # persistent flame into the enemy/idle sprite.
        return image,rect

    def project(self,x,y,z=0):
        dx,dy=x-self.player[0],y-self.player[1]
        depth=dx*math.cos(self.angle)+dy*math.sin(self.angle)
        if depth<.12: return None
        side=-dx*math.sin(self.angle)+dy*math.cos(self.angle)
        focal=W/(2*math.tan(FOV/2))*(2.5 if self.ads and self.weapon_index==3 else 1.4 if self.ads else 1)
        zoom=2.5 if self.ads and self.weapon_index==3 else 1.4 if self.ads else 1
        return (int(W/2+side/depth*focal),int(H/2+self.pitch*H*.72-(z-self.z)/depth*H*.55*zoom))

    def run(self):
        try:
            self._run_loop()
        finally:
            self._capture_mouse(False)
            pygame.quit()

    def _run_loop(self):
        running = True
        while running:
            dt=min(.05,self.clock.tick(60)/1000)
            if self.state=='boss_intro' and pygame.time.get_ticks()-self.boss_intro_start>=self.boss_intro_duration():
                self.wave=self.pending_boss_wave
                self.spawn_wave(); self.begin_wave()
            if self.state=='wave' and pygame.time.get_ticks()>=self.wave_deadline:
                self.state='playing'; self._capture_mouse(True)
            if self.state=='playing': self.now += dt*1000
            now=self.now
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT:
                    running = False
                    break
                if ev.type==pygame.KEYDOWN and ev.key in (pygame.K_TAB,pygame.K_c):
                    if self.state=='character':
                        self.state=self.character_from
                        if self.state=='paused': self.resume()
                    elif self.state in ('playing','wave','menu','paused'):
                        if self.state in ('playing','wave'): self.pause()
                        self.character_from=self.state
                        self.state='character'; self._capture_mouse(False)
                    continue
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE and self.state=='character':
                    self.state=self.character_from
                    if self.state=='paused': self.resume()
                    continue
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_q:
                    running = False
                    break
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_m:
                    self.muted=not self.muted
                    if self.muted and self.reload_channel: self.reload_channel.stop()
                    if self.music_loaded: pygame.mixer.music.set_volume(0 if self.muted else .3)
                    continue
                if self.state=='boss_intro':
                    if ev.type==pygame.KEYDOWN and ev.key in (pygame.K_SPACE,pygame.K_RETURN,pygame.K_ESCAPE):
                        self.boss_intro_start=pygame.time.get_ticks()-self.boss_intro_duration()
                    continue
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_f:
                    self.refill_reserve(); continue
                if ev.type==pygame.WINDOWFOCUSLOST:
                    self.focused=False; self.pause(); continue
                if ev.type==pygame.WINDOWFOCUSGAINED:
                    self.focused=True; continue
                if self.state=='menu':
                    if ((ev.type==pygame.KEYDOWN and ev.key==pygame.K_RETURN) or
                        (ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1 and pygame.Rect(W//2-120,415,240,55).collidepoint(ev.pos))):
                        self.begin_wave()
                    continue
                if self.state=='upgrade':
                    if ev.type==pygame.KEYDOWN and ev.key in (pygame.K_1,pygame.K_2,pygame.K_3): self.choose_upgrade(ev.key-pygame.K_1)
                    elif ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                        for i in range(3):
                            if pygame.Rect(35+i*305,245,285,210).collidepoint(ev.pos): self.choose_upgrade(i); break
                    continue
                if ev.type==pygame.KEYDOWN and ev.key in (pygame.K_1,pygame.K_2,pygame.K_3):
                    self.switch_slot(ev.key-pygame.K_1); continue
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_4:
                    # Compatibility for scripted/legacy tests; real player slots are 1–3.
                    if len(self.weapon_slots) >= 4:
                        self.switch_weapon(3)
                    continue
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
                    if self.state in ('playing','wave'): self.pause()
                    elif self.state == "paused" and self.focused: self.resume()
                    continue
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_SPACE and self.state=='playing':
                    self.jump()
                    continue
                if self.state=='wave': continue
                if ev.type==pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_r) and self.state in ("won","lost"):
                    self.reset(); continue
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_r and self.state == "paused":
                    self.reset(); continue
                if ev.type==pygame.MOUSEMOTION and self.state == "playing":
                    self.angle += ev.rel[0]*0.0025; self.pitch = max(-0.35,min(0.35,self.pitch-ev.rel[1]*0.002))
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==3 and self.state=='playing':
                    if WEAPONS[self.weapon_index].get('kind') in ('melee','shield'):
                        self.combat.attack(now,3); self.guard_damage_reduction=.55 if WEAPONS[self.weapon_index].get('kind')=='shield' else .25
                    else: self.ads=True
                if ev.type==pygame.MOUSEBUTTONUP and ev.button==3:
                    self.ads=False; self.guarding=False; self.guard_damage_reduction=0.0
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    if not self.combat.attack(now,1): self.shoot(now)
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_r and self.state == "playing": self.reload(now)
            if not running:
                break
            if self.state=='playing' and pygame.mouse.get_pressed()[0]:
                if not self.combat.attack(self.now,1): self.shoot(self.now)
            self.update(dt,self.now); self.draw()

if __name__ == '__main__': Game(show_menu=True).run()


