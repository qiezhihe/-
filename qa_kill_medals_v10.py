import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import pygame
from fps_game import Game
G=Game(muted=True);G.terrain_cells=set();G.xp_needed=100000
for now,method,expected in [(100,'headshot',1),(2100,'melee',2),(4101,'normal',1)]:
 e=[18.,14.,10.,0,10.,'normal',999999];G.enemies=[e]
 G.damage_enemy(e,20,now,method=method);G.finish_kills(now)
 assert G.kill_streak==expected,(now,G.kill_streak)
 if now==2100: assert G.streak_methods=={'headshot':1,'melee':1}
assert G.streak_methods=={'headshot':0,'melee':0}
for i in range(6):
 now=4200+i*100;e=[18.,14.,10.,0,10.,'normal',999999];G.enemies=[e]
 G.damage_enemy(e,20,now,method='headshot' if i%2 else 'melee');G.finish_kills(now)
G.enemies=[[18.,14.,100.,0,100.,'normal',999999]];G.now=now;G.state='playing';G.draw()
assert all('icon_kill_'+k in G.cloud_art.images for k in ('1','2','3','4','5','6','7','headshot','melee'))
pygame.image.save(G.screen,'artifacts/kill_medals_v10_live.png');pygame.quit()
print('PASS 2000ms inclusive, 2001ms reset, fatal method counts, 7 kill medal and bottom HUD render')
