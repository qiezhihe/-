import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import math
import unittest
from collections import defaultdict
from unittest.mock import patch
import pygame
from fps_game import Game
from rogue_content import BALANCE


class MovementSpeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.g=Game(muted=True)
    @classmethod
    def tearDownClass(cls):pygame.quit()

    def setUp(self):
        g=self.g;g.state='playing';g.enemies=[];g.projectiles=[]
        g.terrain_cells.clear();g.lava_cells.clear();g.terrain_phase=0
        g.player=[14.,14.];g.angle=g.z=g.vertical_velocity=0
        g.move_speed=BALANCE['player_walk_speed'];g.stamina=100;g.wave_wait=0
        g.pet['type']='none';g.combat.throws.clear();g.evolutions.clear()

    def distance(self,sprint=False,diagonal=False,stamina=100):
        g=self.g;g.player=[14.,14.];g.stamina=stamina
        keys=defaultdict(int,{pygame.K_w:1,pygame.K_LSHIFT:int(sprint),pygame.K_d:int(diagonal)})
        with patch('pygame.key.get_pressed',return_value=keys):g.update(.1,1000)
        return math.dist(g.player,[14.,14.])

    def test_walk_speed_slightly_above_early_runner(self):
        runner=1.4*(1+.015)
        self.assertGreater(self.g.move_speed,runner)
        self.assertLess(self.g.move_speed,runner*1.15)
        self.assertAlmostEqual(self.distance(),.16)

    def test_actual_sprint_is_twice_actual_walk(self):
        self.assertAlmostEqual(self.distance(True),self.distance()*2)
        self.assertAlmostEqual(self.distance(True),.32)

    def test_upgraded_speed_keeps_double_sprint(self):
        self.g.move_speed*=1.24
        self.assertAlmostEqual(self.distance(True),self.distance()*2)

    def test_diagonal_has_no_extra_speed(self):
        self.assertAlmostEqual(self.distance(diagonal=True),self.distance())
        self.assertAlmostEqual(self.distance(True,True),self.distance(True))

    def test_empty_stamina_prevents_sprint(self):
        self.assertAlmostEqual(self.distance(True,stamina=0),.16)


if __name__=='__main__':unittest.main()
