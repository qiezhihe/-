"""Headless screenshots of each gun's independent ammo and ammo-free melee HUD."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from fps_game import Game

g=Game(muted=True);g.unlocked_weapons=set(range(8));g.state='playing'
g.enemies=[];g.player=[10.,14.];g.angle=0;g.now=1000
out=ROOT/'artifacts';out.mkdir(exist_ok=True)
gallery=pygame.Surface((1920,2400))
for index in range(8):
    g.switch_weapon(index);g.message='独立备弹 / 近战无需弹药'
    g.draw();gallery.blit(g.screen,((index%2)*960,(index//2)*600))
    if index in (0,4):
        pygame.image.save(g.screen,str(out/f'weapon_balance_v29_{index}.png'))
    if index==3:
        g.state='character';g.draw()
        pygame.image.save(g.screen,str(out/'weapon_balance_v29_character.png'))
        g.state='playing'
pygame.image.save(gallery,str(out/'weapon_balance_v29_all.png'))
pygame.quit();print('Saved v29 ammo HUD screenshots to artifacts')
