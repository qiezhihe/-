"""Capture the actual reward renderer and every live evolution effect."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pygame
from fps_game import Game
from rogue_content import UPGRADES
from weapon_evolutions import EVOLUTIONS


def main():
    out=ROOT/'artifacts';out.mkdir(exist_ok=True)
    g=Game(muted=True);g.unlocked_weapons=set(range(8));g.weapon_slots=list(range(8));g.terrain_cells.clear()
    g.player=[10.,14.];g.angle=0;g.now=1000;g.enemies=[]
    gallery=pygame.Surface((1140,580));gallery.fill((8,12,18))
    for i,card in enumerate(EVOLUTIONS):
        g.choices=[card,UPGRADES[0],UPGRADES[1]]
        g.state='upgrade';g.reward_is_boss=True;g.draw()
        gallery.blit(g.screen.subsurface(g.upgrade_card_rect(0)),((i%4)*285,(i//4)*290))
    pygame.image.save(gallery,str(out/'weapon_evolution_cards_v28.png'))
    g.choices=[UPGRADES[0],UPGRADES[1],EVOLUTIONS[0]];g.draw()
    pygame.image.save(g.screen,str(out/'weapon_evolution_reward_v28.png'))
    battle=pygame.Surface((960*4,600*2))
    for i in range(8):
        g.state='playing';g.evolutions.clear();g.evolutions.owned=set(range(8))
        g.combat.throws.clear();g.combat.active.clear();g.combat.cooldown=0
        g.player=[10.,14.];g.angle=0;g.stamina=100;g.switch_weapon(i)
        g.enemies=[[15.,14.,10000.,0,10000.,'normal',99999],
                   [16.,15.,10000.,0,10000.,'normal',99999],
                   [17.,14.,10000.,0,10000.,'normal',99999]]
        target=g.enemies[0]
        if i<4:
            for _ in range(8 if i==2 else 1):g.evolutions.gun_shot(i,[(5,target,False)],g.damage,1000)
            g.evolutions.update(.15,1150)
        else:
            g.combat.attack(1000)
            if i==5:g.combat.update(.25,1250)
            if i==6:
                g.combat.update(.25,1250)
                g.combat.update(.25,1500)
            g.evolutions.update(.25,1250)
        g.draw();battle.blit(g.screen,((i%4)*960,(i//4)*600))
    pygame.image.save(battle,str(out/'weapon_evolution_combat_v28.png'))
    pygame.quit();print(out/'weapon_evolution_cards_v28.png')


if __name__=='__main__':main()
