import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest,pygame
from fps_game import Game
class DaggerAudioTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.g=Game(muted=True)
 @classmethod
 def tearDownClass(cls):pygame.quit()
 def test_user_dagger_clip_is_loaded(self):self.assertIn('dagger_dash',self.g.sounds)
 def test_muted_dagger_path_is_safe(self):self.g.muted=True;self.g.sound('dagger_dash')
if __name__=='__main__':unittest.main()
