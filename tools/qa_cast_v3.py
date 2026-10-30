"""Check complete casts, slower walk timing and hit/death pose selection."""
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
    prefix=f'anime_enemy_{unit}_cast3_'
    for i in range(16):
        assert g.enemy_art.cloud[prefix+str(i)].get_bounding_rect().height>20
    e=[18.,14.,100,0,100,unit,0]
    interval=140 if unit=='bat' else 190
    for i in range(8):
        g.now=i*interval
        g.enemy_art.visual(g,e,480,100,state='walk_left')
        assert (prefix+str(i),128) in g.enemy_art.cache or any(k[0]==prefix+str(i) for k in g.enemy_art.cache)
    for state,pose in [('idle',8),('hit',12),('dead',15),('attack_ready',9),('attack_swing',10),('attack_recover',11)]:
        g.enemy_art.visual(g,e,480,100,state=state)
        if state=='idle' and unit=='bat': continue
        assert any(k[0]==prefix+str(pose) for k in g.enemy_art.cache),(unit,state)
pygame.quit()
print('PASS: 96 coherent cast frames, slower locomotion and combat overrides')
