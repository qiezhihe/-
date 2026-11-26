import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest,pygame
from fps_game import Game
class StaminaHudTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.g=Game(muted=True)
 @classmethod
 def tearDownClass(cls):pygame.quit()
 def setUp(self):
  g=self.g;g.state='playing';g.now=1000;g.stamina=g.max_stamina;g.stamina_regen_delay=0
 def test_spend_and_regen(self):
  g=self.g;self.assertTrue(g.spend_stamina(28,1000));self.assertEqual(g.stamina,72);self.assertFalse(g.spend_stamina(100,1000));g.update_stamina(.5,1200);self.assertEqual(g.stamina,72);g.update_stamina(.5,1700);self.assertGreater(g.stamina,72)
 def test_sprint_drains_to_zero(self):
  g=self.g;g.stamina=10;g.update_stamina(.2,1000,True);self.assertAlmostEqual(g.stamina,6);g.update_stamina(.2,1200,True);self.assertAlmostEqual(g.stamina,2)
 def test_blink_spends_or_refuses(self):
  g=self.g;g.unlocked_weapons.add(7);g.switch_weapon(7);g.enemies=[];g.player=[14.,14.];g.stamina=28;g.combat.attack(1000);self.assertEqual(g.stamina,0);g.combat.active.clear();origin=list(g.player);g.combat.attack(2000);self.assertEqual(g.player,origin);self.assertIn('精力不足',g.message)
 def test_hud_smoke(self):self.g.draw();self.assertGreaterEqual(self.g.stamina,0)
if __name__=='__main__':unittest.main()
