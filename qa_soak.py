"""Deterministic headless gameplay soak/performance diagnostic, not a user launcher."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import json
import random
import statistics
import time
import argparse
import pygame
from fps_game import Game


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--waves',type=int,default=100)
    parser.add_argument('--frames',type=int,default=120)
    args=parser.parse_args()
    random.seed(881)
    started_all=time.perf_counter()
    game=Game()
    samples=[]
    maximum_projectiles=0
    try:
        game.unlocked_weapons=set(range(4))
        game.max_hp=game.hp=10000000
        for wave in range(1,args.waves+1):
            game.wave=wave
            game.enemies=[]
            game.spawn_wave()
            game.state='playing'
            game.switch_weapon((wave-1)%4)
            for frame in range(args.frames):
                game.now+=1000/60
                game.angle+=.005
                game.move(.005, -.004)
                game.update(1/60,game.now)
                if game.state=='upgrade':
                    game.choose_upgrade(0)
                if frame%10==0:
                    started=time.perf_counter()
                    game.draw()
                    samples.append((time.perf_counter()-started)*1000)
                maximum_projectiles=max(maximum_projectiles,len(game.projectiles))
                assert 0<=game.reserve<=game.reserve_max
                assert 0<=game.mag<=game.mag_size
                assert all(len(e)==7 for e in game.enemies)
            if wave%50==0:
                print(f'Completed {wave}/{args.waves} waves',flush=True)
        print(json.dumps({'waves':args.waves,'simulation_frames':args.waves*args.frames,'render_samples':len(samples),
                          'elapsed_seconds':round(time.perf_counter()-started_all,2),
                          'render_ms_mean':round(statistics.mean(samples),2),
                          'render_ms_p95':round(sorted(samples)[int(len(samples)*.95)],2),
                          'render_ms_max':round(max(samples),2),
                          'maximum_projectiles':maximum_projectiles},indent=2))
    finally:
        game._capture_mouse(False)
        pygame.quit()


if __name__=='__main__':
    main()
