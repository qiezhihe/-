"""Verify generated cycles and runtime frame selection, including combat overrides."""
import os
import sys
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from fps_game import Game

g=Game()
for unit in ('normal','runner','shooter','tank','elite','bat'):
    e=[18.,14.,100,0,100,unit,0]
    prefix=f'anime_enemy_{unit}'
    for i in range(8):
        key=f'{prefix}_locomotion_{i}'
        assert key in g.enemy_art.cloud, key
        assert g.enemy_art.cloud[key].get_bounding_rect().height>50,key
        g.now=i*(140 if unit=='bat' else 190)
        image,rect=g.enemy_art.visual(g,e,480,100,state='walk_left')
        active=f'{prefix}_cast3_{i}' if prefix+'_cast3_8' in g.enemy_art.cloud else key
        assert any(k[0]==active for k in g.enemy_art.cache),active
    for state in ('hit','dead','attack_ready','attack_swing','attack_recover'):
        g.enemy_art.visual(g,e,480,100,state=state)
pygame.quit()
print('PASS: 48 generated locomotion frames selected; combat poses render')
