"""Verify every required motion frame exists, is nonempty and can render."""
import os
import sys
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from fps_game import Game

g=Game(); g.state='playing'
names=('smg','shotgun','mg','sniper','sword','boomerang','spear','dagger')
units=('normal','runner','shooter','tank','elite','bat','boss_fan','boss_dash','boss_ring')
folder=Path(__file__).resolve().parents[1]/'Assets/Art/pixel_portal_v1/runtime'
paths=[folder/f'low_{name}_anim_{i}.png' for name in names for i in range(16)]
paths += [folder/f'{unit}_motion_{i}.png' for unit in units for i in range(16)]
paths += [folder/f'pet_{name}_motion_{i}.png' for name in ('healer','taunter','gunner','minelayer','berserker') for i in range(8)]
for path in paths:
    frame=pygame.image.load(str(path)).convert_alpha()
    assert frame.get_bounding_rect().width>0, path
    g.screen.blit(frame,(0,0))
for index in range(8):
    g.weapon_index=index
    for i in range(16):
        g.now=1000+i*20; g.weapon_action_start=1000
        g.cloud_art.weapon(g)
for unit in units:
    kind='boss' if unit.startswith('boss_') else unit
    g.wave={'boss_fan':5,'boss_dash':10,'boss_ring':15}.get(unit,1)
    e=[18.,14.,100,0,100,kind,0]
    for i in range(16):
        g.now=i*110
        g.enemy_art.visual(g,e,480,100)
pygame.quit()
print(f'PASS: {len(paths)} required motion frames loaded, nonempty; weapon/enemy render coverage OK')
