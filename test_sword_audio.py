import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest,pygame
from fps_game import Game
class SwordAudioTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.g=Game(muted=True)
 @classmethod
 def tearDownClass(cls):pygame.quit()
 def test_user_sword_clip_is_loaded(self):self.assertIn('sword_swing',self.g.sounds)
 def test_muted_sword_path_is_safe(self):self.g.muted=True;self.g.sound('sword_swing')
if __name__=='__main__':unittest.main()
