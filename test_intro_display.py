"""Verify the actual draw entry point presents boss scenes to the window."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
from unittest.mock import patch
import pygame
from fps_game import Game,W,H

class IntroDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.g=Game()
    @classmethod
    def tearDownClass(cls): pygame.quit()

    def test_intro_presents_each_scene_and_resets_clip(self):
        g=self.g; g.state='boss_intro'; g.pending_boss_wave=5; g.boss_intro_start=1000
        images=[]
        for elapsed in (0,2500,5000):
            g.screen.set_clip((0,0,10,10))
            with patch('pygame.time.get_ticks',return_value=1000+elapsed), patch('pygame.display.flip') as flip:
                g.draw()
                flip.assert_called_once()
            self.assertEqual(g.screen.get_clip(),pygame.Rect(0,0,W,H))
            images.append(pygame.image.tobytes(g.screen,'RGB'))
        self.assertNotEqual(images[0],images[1])
        self.assertNotEqual(images[1],images[2])

    def test_world_draw_has_no_bottom_cutoff(self):
        g=self.g; g.state='playing'; g.enemies=[]
        clips=[]
        original=g.map_art.draw_ground
        def ground(game):
            clips.append(game.screen.get_clip())
            return original(game)
        with patch.object(g.map_art,'draw_ground',side_effect=ground): g.draw()
        self.assertTrue(clips)
        self.assertEqual(clips[0],pygame.Rect(0,0,W,H))
        pygame.image.save(g.screen,'artifacts/full_ground_fix.png')

if __name__=='__main__': unittest.main()
