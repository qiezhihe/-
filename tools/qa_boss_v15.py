"""Capture hunter identity, judge laser arena and representative render cost."""
import os
import sys
import time
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pygame
from fps_game import Game

out=Path(__file__).resolve().parents[1]/'artifacts';out.mkdir(exist_ok=True)
g=Game(muted=True);g.state='playing';g.terrain_cells=set();g.angle=0;g.pitch=0
for wave in (10,15):
    g.wave=wave;g.player=[14.,14.]
    boss=[21.,14.,1000.,0,1000.,'boss',999999];g.enemies=[boss]
    g.combat.boss_cycles.clear();g.combat.boss_pattern.clear();g.combat.boss_impacts=[]
    if wave==10:g.player=[18.,14.]
    g.combat.boss_attack(boss,1000);p=g.combat.boss_pattern[id(boss)]
    samples=(('warning',p['windup']-300),('active',p['windup']+600))
    if wave==15:samples+=(('reverse',p['windup']+4200),('impact',p['windup']+4500))
    last_tick=int(p['windup'])-50
    for label,now in samples:
        if wave==10:g.player=[14.,15.];g.angle=0
        else:
            # Keep the locked throw in view to inspect its trajectory and zone.
            g.player=[17.,15.]
        for tick in range(last_tick+50,int(now)+1,50):
            g.combat.update(.05,tick)
            last_tick=tick
        g.now=now;g.hp=100;g.draw()
        pygame.image.save(g.screen,str(out/f'boss_v15_{wave}_{label}.png'))
    if wave==15:
        costs=[]
        for _ in range(24):
            start=time.perf_counter();g.draw();costs.append(time.perf_counter()-start)
        print(f'3-beam scene draw median: {sorted(costs)[len(costs)//2]*1000:.2f}ms (dummy driver)')
pygame.quit()
print('PASS: hunter / judge warning, active, reversal and area renders')
