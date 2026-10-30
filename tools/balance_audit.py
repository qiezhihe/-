"""Offline content audit, not a substitute for real aim/avoidance playtesting."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rogue_content import UPGRADES, WEAPONS


def sustained_dps(weapon, damage_factor=1, rate_factor=1, reload_factor=1):
    damage = weapon['damage'] * weapon['pellets'] * damage_factor
    cycle = weapon['mag'] * weapon['delay'] / rate_factor + weapon['reload'] / reload_factor
    return damage * weapon['mag'] / (cycle / 1000)


def main():
    assert len(UPGRADES) >= 100
    assert len({(card[0],card[3]) for card in UPGRADES}) == len(UPGRADES)
    assert all(card[1] and card[2] and 0 <= card[3] <= 3 and math.isfinite(card[4]) for card in UPGRADES)
    print(f'cards={len(UPGRADES)}, effects={len({card[0] for card in UPGRADES})}')
    print('Theoretical sustained DPS: all pellets hit, no misses, reload included')
    for weapon in WEAPONS:
        print(f"{weapon['name']}: {sustained_dps(weapon):.1f}")
    print('Boss HP and unupgraded SMG ideal seconds (other enemies excluded)')
    for wave in (5,10,20,50,100,500,1000):
        hp=(45+12*wave)*12
        print(f'wave={wave}, hp={hp}, smg_seconds={hp/sustained_dps(WEAPONS[0]):.1f}')
    print('Repeated common damage cards: compare growth to linear Boss HP')
    for stacks in (10,25,50,100,500):
        factor=1.12**stacks
        assert math.isfinite(factor)
        print(f'stacks={stacks}, damage_factor={factor:.4g}')
    print('Audit passed. Wave simulation only covers formulas, not survivability.')


if __name__ == '__main__':
    main()
