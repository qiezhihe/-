"""Capture release edge-case screenshots with the real renderer."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
from pathlib import Path
import pygame
from fps_game import Game


def main():
    output=Path(__file__).resolve().parent/'qa_screenshots'
    output.mkdir(exist_ok=True)
    game=Game()
    try:
        game.state='playing'
        game.enemies=[]
        game.unlocked_weapons=set(range(4))
        game.reserve=2
        game.hp=25
        game.wave=100
        game.now=1000
        game.switch_weapon(1)
        game.mag=1
        game.enemies=[[14.6,14,100,0,100,'elite',0],[19,14,5000,0,5000,'boss',0],
                      [17,12,500,0,500,'shooter',0],[17,16,500,0,500,'runner',0]]
        game.attack_animations[id(game.enemies[0])]=('melee',1500)
        game.projectiles=[[14.25+i*.25,14+((i%3)-1)*.25,-5,0,100,3000] for i in range(20)]
        game.draw()
        pygame.image.save(game.screen,str(output/'close_melee_bullet_low_ammo.png'))
        game.switch_weapon(3)
        game.ads=True
        game.draw()
        pygame.image.save(game.screen,str(output/'sniper_ads_boss_hud.png'))
        game.offer_upgrade(True)
        game.draw()
        pygame.image.save(game.screen,str(output/'boss_rewards.png'))
        print(str(output))
    finally:
        game._capture_mouse(False)
        pygame.quit()


if __name__=='__main__':
    main()
