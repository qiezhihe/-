import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest,pygame
from fps_game import Game
class DamageFeedbackTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.g=Game(muted=True)
 @classmethod
 def tearDownClass(cls):pygame.quit()
 def setUp(self):
  g=self.g;g.state='playing';g.now=1000;g.enemies=[];g.damage_popups=[];g.reserve=77;g.wave=1;g.weapon_ammo[g.weapon_index]=g.mag
 def popup(self,**kwargs):
  g=self.g;e=[18.,14.,100.,0,100.,'normal',0];g.enemies=[e];g.damage_enemy(e,10,g.now,**kwargs);return g.damage_popups[-1]
 def test_critical_is_yellow(self):self.assertEqual(self.popup(critical=True)['color'],'yellow')
 def test_noncritical_head_is_red_and_above_body(self):
  p=self.popup(headshot=True);self.assertEqual(p['color'],'red');self.assertGreater(p['hit_z'],.68)
 def test_noncritical_body_is_white(self):self.assertEqual(self.popup()['color'],'white')
 def test_headshot_critical_has_yellow_priority(self):
  p=self.popup(headshot=True,critical=True);self.assertEqual(p['color'],'yellow');self.assertEqual(p['hit_z'],1.12)
 def test_rendered_damage_numbers_increase_in_size(self):
  labels=[self.g.damage_number_label({'color':c,'amount':100}) for c in ('white','red','yellow')]
  self.assertLess(labels[0].get_height(),labels[1].get_height());self.assertLess(labels[1].get_height(),labels[2].get_height())
  self.assertLess(labels[0].get_width(),labels[1].get_width());self.assertLess(labels[1].get_width(),labels[2].get_width())
 def test_critical_head_and_body_stay_at_separate_hit_positions(self):
  g=self.g;e=[18.,14.,100.,0,100.,'normal',0];g.enemies=[e]
  g.damage_enemy(e,5,g.now,critical=True);g.damage_enemy(e,5,g.now,critical=True,headshot=True)
  self.assertEqual(len(g.damage_popups),2);self.assertNotEqual(g.damage_popups[0]['hit_z'],g.damage_popups[1]['hit_z'])
 def test_different_types_do_not_merge(self):
  g=self.g;e=[18.,14.,100.,0,100.,'normal',0];g.enemies=[e];g.damage_enemy(e,5,g.now,headshot=True);g.damage_enemy(e,5,g.now,critical=True);self.assertEqual(len(g.damage_popups),2)
 def test_wave_preserves_reserve(self):
  g=self.g;g.reserve=17;g.spawn_wave();self.assertEqual(g.reserve,17);self.assertEqual(g.mag,g.mag_size)
if __name__=='__main__':unittest.main()
