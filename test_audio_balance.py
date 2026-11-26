import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest,wave,struct,pygame
from fps_game import Game
class AudioBalanceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.g=Game(muted=True)
 @classmethod
 def tearDownClass(cls):pygame.quit()
 def test_footstep_is_centered_stereo(self):
  with wave.open('Assets/audio/footstep.wav','rb') as w:
   self.assertEqual(w.getnchannels(),2);vals=struct.unpack('<'+'h'*(w.getnframes()*2),w.readframes(w.getnframes()))
  self.assertTrue(all(vals[i]==vals[i+1] for i in range(0,len(vals),2)))
 def test_sword_attack_rate_and_loudness(self):
  from rogue_content import WEAPONS
  self.assertEqual(WEAPONS[4]['delay'],600);self.assertAlmostEqual(self.g.sounds['sword_swing'].get_volume(),.78,places=1)
if __name__=='__main__':unittest.main()
