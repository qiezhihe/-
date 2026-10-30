"""Accelerated real wave/reward progression; kills are injected, transitions are real."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import json
import random
import time
import pygame
from fps_game import Game


def main():
    random.seed(735)
    started=time.perf_counter()
    game=Game()
    selections=0
    try:
        game.focused=True
        for wave in range(1,151):
            assert game.wave==wave,(game.wave,wave)
            # Fast-forward real 3-second presentation as run() does; keep game time paused.
            assert game.state=='wave'
            game.state='playing'
            game.projectiles.append([14,14,1,0,3,game.now+5000])
            for enemy in game.enemies:
                enemy[2]=0
            game.finish_kills(game.now)
            while game.state=='upgrade':
                before=game.xp
                game.choose_upgrade(random.randrange(3))
                selections+=1
                assert selections<10000,'upgrade chain did not converge'
            game.now+=150
            game.update(.01,game.now)
            assert not game.projectiles,'old bullets survived wave transition'
            assert game.state=='wave'
            assert game.wave==wave+1
            assert 0<=game.reserve<=game.reserve_max
            assert 0<=game.mag<=game.mag_size
            if wave%10==0:
                game.draw()
        print(json.dumps({'completed_waves':150,'selected_upgrade_cards':selections,
                          'level':game.level,'unlocked_weapons':sorted(game.unlocked_weapons),
                          'damage':round(game.damage,2),'fire_delay_ms':round(game.fire_delay,2),
                          'elapsed_seconds':round(time.perf_counter()-started,2)},indent=2))
    finally:
        game._capture_mouse(False)
        pygame.quit()


if __name__=='__main__':
    main()
