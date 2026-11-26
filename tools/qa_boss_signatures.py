"""Exercise all signature encounters through windup, release and recovery."""
import os,sys
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from fps_game import Game

g=Game(); g.state='playing'; g.terrain_cells=set()
for index,skill in enumerate(('hammer','hunt','snipe','brood','duel')):
    for enraged in (False,True):
        g.wave=(index+1)*5; g.player=[14.,14.]; g.hp=1000
        e=[10.,14.,400 if enraged else 1000,0,1000,'boss',999999]
        g.enemies=[e]; g.projectiles=[]; g.combat.boss_pattern.clear()
        g.combat.boss_cycles[id(e)]=1 if skill=='snipe' else 0
        assert g.combat.boss_attack(e,1000)
        pattern=g.combat.boss_pattern[id(e)]
        assert pattern['skill']==skill
        hp=g.hp; g.combat.update(.016,pattern['windup']-1)
        assert g.hp==hp, 'windup damaged player'
        for now in range(pattern['windup'],pattern['recover'],50):
            g.now=now; g.combat.update(.05,now)
        assert len(g.enemies)<=4, 'unbounded summons'
        g.combat.update(.05,pattern['recover']+1)
        assert id(e) not in g.combat.boss_pattern
        g.draw()
pygame.quit()
print('PASS: five signatures, both phases, safe windup and finite recovery')
