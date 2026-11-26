"""Render the actual weapon selector, including idle -> reload -> idle."""
import os
import sys
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from PIL import Image
from fps_game import Game

out=Path(__file__).resolve().parents[1]/'artifacts';out.mkdir(exist_ok=True)
g=Game(muted=True);g.state='playing';g.unlocked_weapons.add(2);g.switch_weapon(2)
g.terrain_cells=set();g.enemies=[[20.,14.,100,0,100,'normal',999999]]
g.angle=0;g.now=10000;g.mag=5;g.reserve=200;g.weapon_action_start=-100000
g.draw();idle=g.screen.copy()
g.reload(g.now)
frames=[Image.frombytes('RGB',idle.get_size(),pygame.image.tobytes(idle,'RGB'))]
for index in range(8):
    g.now=g.reload_start+g.reload_duration*(index+.5)/8
    g.cloud_art.cache.clear();g.draw()
    assert any(key[0]==f'low_mg_reload_v16_{index}' for key in g.cloud_art.cache)
    frames.append(Image.frombytes('RGB',g.screen.get_size(),pygame.image.tobytes(g.screen,'RGB')))
    if index==5:pygame.image.save(g.screen,str(out/'mg_reload_v16_ingame.png'))
frames.append(frames[0])
frames[0].save(out/'mg_reload_v16_preview.gif',save_all=True,append_images=frames[1:],
               duration=[650]+[round(g.reload_duration/8)]*8+[650],loop=0)
pygame.quit()
print('PASS: in-game reload sequence; saved preview GIF and screenshot')
