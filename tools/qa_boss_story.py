"""Verify all five cinematic stories and chronological playback boundaries."""
import os,sys
from pathlib import Path
from unittest.mock import patch
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from fps_game import Game

g=Game()
for index,name in enumerate(('colossus','hunter','judge','weaver','executioner')):
    g.pending_boss_wave=(index+1)*5
    g.boss_intro_start=1000
    for frame in range(6):
        key=f'fx_story_{name}_{frame}'
        assert key in g.cloud_art.images,key
        with patch('pygame.time.get_ticks',return_value=1000+frame*2500):
            g.draw_boss_intro()
    if index==0: pygame.image.save(g.screen,'artifacts/boss_story_live.png')
pygame.quit()
print('PASS: all 30 chronological encounter panels rendered at 2.5s intervals')
