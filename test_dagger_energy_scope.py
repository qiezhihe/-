import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
from unittest.mock import patch
import pygame
from fps_game import Game
from rogue_content import EFFECTS,SPECIALS,UPGRADES


class DaggerEnergyScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.g=Game(muted=True)
    @classmethod
    def tearDownClass(cls):pygame.quit()

    def setUp(self):
        g=self.g;g.unlocked_weapons=set(range(8));g.weapon_slots=[0,1,3]
        g.blink_stamina_cost=28;g.extras.clear();g.upgrade_stacks.clear()
        g.boss_rewards=0;g.xp=0;g.focused=True;g.switch_weapon(0)

    def test_blink_card_is_dagger_special_not_universal(self):
        self.assertNotIn('blink_efficiency',{x[0] for x in EFFECTS})
        self.assertIn(('blink_efficiency',7),{(x[0],x[3]) for x in SPECIALS})
        cards=[x for x in UPGRADES if x[0]=='blink_efficiency']
        self.assertEqual(len(cards),4)
        self.assertTrue(all('闪现短刃' in c[1] and '仅闪现短刃' in c[2] for c in cards))

    def check_pools(self,expect):
        g=self.g;pools=[]
        def choose(pool,weights=None,**kwargs):
            if isinstance(pool,range):return [0]
            pools.append({c[0] for c in pool})
            return [pool[0]]
        with patch('fps_game.random.choices',side_effect=choose),patch.object(g,'offer_pet_upgrade'),patch.object(g.evolutions,'offer',return_value=None):
            for boss in (False,True):g.offer_upgrade(boss)
        self.assertTrue(all(('blink_efficiency' in p)==expect for p in pools))

    def test_guns_and_other_melee_cannot_offer_card_even_if_dagger_unlocked(self):
        for weapon in range(7):
            self.g.weapon_slots=[weapon];self.check_pools(False)

    def test_dagger_in_inventory_allows_its_card(self):
        self.g.weapon_slots=[0,7];self.check_pools(True)

    def test_nonholder_cannot_apply_stale_card(self):
        g=self.g;g.state='upgrade';g.choices=[next(c for c in UPGRADES if c[0]=='blink_efficiency')]
        g.choose_upgrade(0)
        self.assertEqual(g.blink_stamina_cost,28);self.assertNotIn('blink_efficiency',g.upgrade_stacks)

    def test_card_reduces_dagger_cost_without_changing_other_weapons(self):
        g=self.g;g.weapon_slots=[0,7];g.state='upgrade'
        g.choices=[next(c for c in UPGRADES if c[0]=='blink_efficiency' and c[3]==0)]
        g.choose_upgrade(0);self.assertAlmostEqual(g.blink_stamina_cost,22.4)
        g.stamina=100;g.spend_stamina(g.blink_stamina_cost,1000)
        self.assertAlmostEqual(g.stamina,77.6)
        g.unlocked_weapons.add(4);g.switch_weapon(4);g.combat.cooldown=0;g.enemies=[]
        before=g.stamina;g.combat.attack(2000);self.assertEqual(g.stamina,before)


if __name__=='__main__':unittest.main()
