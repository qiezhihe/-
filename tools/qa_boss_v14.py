"""Render complete Boss silhouettes, world damage footprints and sniper poses."""
import os
import sys
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from fps_game import Game

out=Path(__file__).resolve().parents[1]/'artifacts'
out.mkdir(exist_ok=True)
g=Game(muted=True);g.state='playing';g.player=[14.,14.];g.angle=0;g.pitch=0
g.terrain_cells=set();g.wave=5
boss=[22.,14.,1000.,0,1000.,'boss',999999];g.enemies=[boss]
for now,pose in ((100,'idle'),(1200,'attack'),(2300,'recover')):
    g.now=now
    g.combat.boss_pattern[id(boss)]=dict(skill='hammer',windup=1000,impact=2000,recover=3000,
        stage=0,enraged=False,target=(20.,14.),origin=tuple(boss[:2]))
    g.combat.boss_impacts=[] if pose=='idle' else [(20.,14.,'slam',3000,g.combat.hammer_radius(0))]
    g.draw();pygame.image.save(g.screen,str(out/f'boss_v14_{pose}.png'))
g.combat.boss_pattern.clear();g.combat.boss_impacts=[]
g.unlocked_weapons.add(3);g.switch_weapon(3)
g.weapon_action_start=-10000
for pose in range(16):
    g.screen.fill((28,38,52));g.cloud_art.cache.clear()
    g.now=20000
    if pose>=8:
        g.reload_duration=800;g.reload_start=20000-(pose-8)*100-50;g.reload_until=g.reload_start+800
    else:
        g.reload_until=0;g.muzzle_until=0;g.weapon_action_start=20000-int(max(0,pose-2)*min(700,g.fire_delay)/5+1)
        if pose==0:g.weapon_action_start=-10000
        if pose==1:g.muzzle_until=20070
    g.cloud_art.weapon(g)
    expected=f'low_sniper_v14_{pose}'
    if pose!=7:assert any(key[0]==expected for key in g.cloud_art.cache),expected
g.reload_until=0;g.weapon_action_start=-10000;g.muzzle_until=0;g.draw()
pygame.image.save(g.screen,str(out/'sniper_v14_ingame.png'))
g.now=1000;g.combat.boss_impacts=[(14.,14.,'slam',2000,2.6)]
g.draw();pygame.image.save(g.screen,str(out/'boss_v14_inside_zone.png'))
g.combat.boss_impacts=[]
g.combat.boss_pattern[id(boss)]=dict(skill='laser',origin=tuple(boss[:2]),target=(14.,14.),
    angle=3.14,windup=1000,impact=2600,recover=3400)
g.draw();pygame.image.save(g.screen,str(out/'boss_v14_laser.png'))
pygame.quit()
print('PASS: Boss idle / attack / recovery and all selected sniper animation poses')
