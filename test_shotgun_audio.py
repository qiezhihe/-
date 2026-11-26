import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest,pygame
from fps_game import Game
class ShotgunAudioTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.g=Game(muted=True)
 @classmethod
 def tearDownClass(cls):pygame.quit()
 def test_user_shotgun_clip_is_loaded_loud(self):
  self.assertIn('shot1',self.g.sounds);self.assertAlmostEqual(self.g.sounds['shot1'].get_volume(),.90,delta=.008)
 def test_muted_shotgun_path_is_safe(self):self.g.muted=True;self.g.sound('shot1')
if __name__=='__main__':unittest.main()
