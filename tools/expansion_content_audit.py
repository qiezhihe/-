"""Validate the opt-in expansion catalogue without enabling it in live rewards."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rogue_content import EXPANSION_EFFECTS, EXPANSION_UPGRADES, WEAPONS, expansion_pool

assert len(EXPANSION_EFFECTS) == 25, len(EXPANSION_EFFECTS)
assert len(EXPANSION_UPGRADES) == 100, len(EXPANSION_UPGRADES)
assert len({card[0] for card in EXPANSION_UPGRADES}) == 25
assert len({(card[0], card[3]) for card in EXPANSION_UPGRADES}) == 100
assert len(WEAPONS) == 8
assert [w['name'] for w in WEAPONS[:4]] == ['冲锋枪','霰弹枪','机枪','狙击枪']
assert not expansion_pool(set(), set(), set())
assert all(card[2] and len(card[2]) < 80 for card in EXPANSION_UPGRADES)
print('expansion effects=25, cards=100, weapon slots=3, base weapons=8')
print('live pool remains isolated until implementation keys are registered')
