"""Headless render coverage for the replacement art pack."""
import os
import sys
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from fps_game import Game

g=Game()
for index in range(8):
    g.unlocked_weapons.add(index)
    g.weapon_index=index
    g.state='playing'
    for age in (0,40,100,200):
        g.weapon_action_start=g.now-age
        g.draw()
for wave in (5,10,15):
    g.wave=wave
    g.enemies=[[18.,14.,1000,0,1000,'boss',100000]]
    g.draw()
for typ in ('healer','taunter','gunner','minelayer','berserker'):
    g.pet.update(type=typ,x=17.,y=14.,hp=100,max_hp=100)
    g.draw()
g.state='menu'; g.draw()
pygame.image.save(g.screen,'artifacts/pixel_menu.png')
pygame.quit()
print('8 weapons, 3 bosses, 5 pets and menu render OK')
