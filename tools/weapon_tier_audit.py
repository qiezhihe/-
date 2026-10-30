"""Exercise every weapon-specific effect at each quality through the real game."""
import os
import sys
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from fps_game import Game
from rogue_content import UPGRADES


def main():
    game=Game()
    families={0:['smg_haste','smg_mag'],1:['shot_tight','shot_power','pellets'],
              2:['mg_power','mg_reload'],3:['sniper_power','sniper_haste']}
    tested=0
    try:
        for weapon, keys in families.items():
            for key in keys:
                for rank in range(4):
                    game.reset()
                    game.unlocked_weapons={0,1,2,3}
                    game.switch_weapon(weapon)
                    before=(game.damage,game.fire_delay,game.mag_size,
                            game.reload_duration,game.extras.get(key,0))
                    game.choices=[next(c for c in UPGRADES if c[0]==key and c[3]==rank)]
                    game.state='upgrade'
                    game.choose_upgrade(0)
                    after=(game.damage,game.fire_delay,game.mag_size,
                           game.reload_duration,game.extras.get(key,0))
                    assert before!=after,(weapon,key,rank)
                    assert game.upgrade_stacks[key]==1
                    assert game.fire_delay>=35 and game.reload_duration>=250 and game.mag_size<=500
                    tested+=1
        print(f'Weapon-specific quality cases passed: {tested}')
    finally:
        pygame.quit()


if __name__ == '__main__':
    main()
