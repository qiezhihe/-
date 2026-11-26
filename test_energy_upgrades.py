import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest,pygame
from fps_game import Game
from rogue_content import UPGRADES
class EnergyUpgradeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.g=Game(muted=True)
 @classmethod
 def tearDownClass(cls):pygame.quit()
 def setUp(self):
  g=self.g;g.state='upgrade';g.stamina=40;g.max_stamina=100;g.stamina_drain_rate=20;g.stamina_regen_rate=12;g.blink_stamina_cost=28;g.extras.clear();g.upgrade_stacks.clear();g.weapon_ammo.clear()
 def choose(self,key):
  g=self.g;g.choices=[next(x for x in UPGRADES if x[0]==key and x[3]==0)];g.choose_upgrade(0)
 def test_cards_are_in_upgrade_pool(self):
  keys={x[0] for x in UPGRADES};self.assertTrue({'stamina_core','stamina_regen','sprint_efficiency','blink_efficiency'}<=keys)
 def test_core_increases_capacity(self):self.choose('stamina_core');self.assertEqual(self.g.max_stamina,115);self.assertEqual(self.g.stamina,55)
 def test_regen_and_cost_cards_apply(self):
  self.choose('stamina_regen');self.assertAlmostEqual(self.g.stamina_regen_rate,14.16,places=2)
  self.g.state='upgrade';self.choose('sprint_efficiency');self.assertAlmostEqual(self.g.stamina_drain_rate,17,places=2)
  self.g.unlocked_weapons.add(7);self.g.weapon_slots=[0,7]
  self.g.state='upgrade';self.choose('blink_efficiency');self.assertAlmostEqual(self.g.blink_stamina_cost,22.4,places=2)
 def test_icons_are_loaded(self):
  for key in ('stamina_core','stamina_regen','sprint_efficiency','blink_efficiency'):
   self.assertIn('icon_'+key,self.g.cloud_art.images)
if __name__=='__main__':unittest.main()
