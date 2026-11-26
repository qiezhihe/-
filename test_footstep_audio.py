import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest,pygame
from fps_game import Game
class FootstepAudioTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.g=Game(muted=True)
 @classmethod
 def tearDownClass(cls):pygame.quit()
 def test_clip_is_loaded(self):self.assertIn('footstep',self.g.sounds)
 def test_footstep_volume_is_raised(self):self.assertAlmostEqual(self.g.sounds['footstep'].get_volume(),.85,delta=.008)
 def test_mute_path_never_raises(self):self.g.muted=True;self.g.sound('footstep')
if __name__=='__main__':unittest.main()
