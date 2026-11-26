import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import pygame
from fps_game import Game
G=Game(muted=True);G.state='playing';G.terrain_cells=set();G.enemies=[]
e=[18.,14.,100.,0,100.,'normal',999999];G.enemies=[e]
assert G.damage_enemy(e,27,100)==27 and e[2]==73
G.damage_enemy(e,200,150);assert e[2]==0 and sum(p['amount'] for p in G.damage_popups)==100
G.finish_kills(150);assert '一杀' in G.kill_popup[0]
for i in range(6):
 e=[18.,14.,0.,0,100.,'normal',999999];G.enemies=[e];G.finish_kills(200+i*100)
assert '杀敌如麻' in G.kill_popup[0]
G.enemies=[[18.,14.,0.,0,100.,'normal',999999]];G.finish_kills(7000);assert G.kill_streak==1
G.state="playing";G.now=7100;G.enemies=[[18.,14.,200.,0,200.,'normal',999999]];G.damage_enemy(G.enemies[0],37,G.now);G.draw();pygame.image.save(G.screen,'artifacts/combat_v9_feedback.png')
for i in range(5):
 G.wave=(i+1)*5;G.now=10000;boss=[19.,14.,500.,0,500.,'boss',999999];G.enemies=[boss]
 G.combat.boss_pattern.clear();G.combat.boss_cycles.clear();G.combat.boss_attack(boss,G.now)
 assert G.combat.boss_pattern[id(boss)]['skill']==('hammer','hunt','laser','brood','duel')[i]
 G.now+=1800;G.draw();pygame.image.save(G.screen,f'artifacts/combat_v9_boss_{i}.png')
G.wave=15;G.now=20000;G.combat.boss_pattern[id(boss)]=dict(skill='laser',origin=tuple(boss[:2]),angle=3.14,windup=19000,impact=22000,recover=23000)
G.draw();pygame.image.save(G.screen,'artifacts/combat_v9_laser.png')
pygame.quit();print('PASS: actual damage, overkill, 1-7 streak, expiry, five signatures and all renders')
