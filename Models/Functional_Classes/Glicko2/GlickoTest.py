import unittest
import math
from Models.Functional_Classes.Glicko2.GlickoFighter import GlickoFighter
from Models.Functional_Classes.Glicko2.GlickoCalculator import GlickoCalculator

class TestGlickoCalculator(unittest.TestCase):

    def setUp(self):
        self.calculator = GlickoCalculator()
        self.fighter = GlickoFighter(rating=1500, rd=350, volatility=0.06)
        self.opponent_strong = GlickoFighter(rating=2000, rd=50, volatility=0.06)
        self.opponent_weak = GlickoFighter(rating=1000, rd=50, volatility=0.06)


    def test_g_phi_bounds(self):

        self.assertAlmostEqual(self.calculator.g_phi(0), 1.0, places=5)
    
        large_rd = 100000
        result = self.calculator.g_phi(large_rd)
        self.assertTrue(0 < result < 0.1, "g")

    def test_expected_outcome_logic(self):

        prob = self.calculator.expected_outcome(0, 0, 1) 
        self.assertAlmostEqual(prob, 0.5, places=5)


    def test_perfect_win_against_strong_opponent(self):
        initial_rating = self.fighter.rating
        
        self.calculator.rate_1vs1(self.fighter, self.opponent_strong, 1.0)
        
        print(f"Upset Win: {initial_rating} -> {self.fighter.rating}")
        self.assertGreater(self.fighter.rating, initial_rating + 100, "Rating should jump")

    def test_perfect_loss_against_weak_opponent(self):
        initial_rating = self.fighter.rating
        
        self.calculator.rate_1vs1(self.fighter, self.opponent_weak, 0.0)
        
        print(f"Upset Loss: {initial_rating} -> {self.fighter.rating}")
        self.assertLess(self.fighter.rating, initial_rating - 100,"Rating should crash after losing")


    def test_rd_decrease_logic(self):

        start_rd = self.fighter.rd
        self.calculator.rate_1vs1(self.fighter, self.opponent_weak, 1.0)
        self.assertLess(self.fighter.rd, start_rd, "RD must decrease after a match")

