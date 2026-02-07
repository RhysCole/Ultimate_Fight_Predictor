import math
from Models.Functional_Classes.Glicko2.GlickoFighter import GlickoFighter
class GlickoCalculator:
    # Constants for Glicko-2 system scaling
    TAU = 0.5 
    SCALING_FACTOR = 173.7178

    def __init__(self):
        self.CONVERGENCE_TOLERANCE = 0.000001

    def rate_1vs1(self, player: GlickoFighter, opponent: GlickoFighter, outcome: float):
        # Helper to process a single match by wrapping inputs in lists
        self.update_player(
            player=player,
            opponent_ratings=[opponent.rating],
            opponent_rds=[opponent.rating_deviation],
            outcomes=[outcome]
        )

    def update_player(self, player: GlickoFighter, opponent_ratings: list, opponent_rds: list, outcomes: list):
        # Convert rating and RD to Glicko-2 scale
        rating_glicko = (player.rating - 1500) / self.SCALING_FACTOR
        rd_glicko = player.rating_deviation / self.SCALING_FACTOR

        # Calculate variance and estimated improvement based on performance
        variance = self.get_variance(rating_glicko, opponent_ratings, opponent_rds)
        improvement = self.get_improvement(variance, rating_glicko, opponent_ratings, opponent_rds, outcomes)
        new_vol = self.calculate_new_volatility(improvement, rd_glicko, variance, player.volatility)

        # Update RD with the new volatility
        pre_rating_rd = math.sqrt(rd_glicko**2 + new_vol**2)
        
        new_rd_glicko = 1.0 / math.sqrt((1.0 / pre_rating_rd**2) + (1.0 / variance))
        
        # Calculate the new rating
        update_sum = self.get_update_sum(rating_glicko, opponent_ratings, opponent_rds, outcomes)
        new_rating_glicko = rating_glicko + new_rd_glicko**2 * update_sum

        # Convert back to standard scale and update player object
        player.rating = 1500 + new_rating_glicko * self.SCALING_FACTOR
        player.rating_deviation =new_rd_glicko * self.SCALING_FACTOR
        player.volatility = new_vol

    def g_phi(self, rd):
        # Calculate impact factor of RD (less reliable opponents have less weight)
        phi = rd / self.SCALING_FACTOR
        return 1.0 / math.sqrt(1.0 + 3.0 * phi**2 / math.pi**2)

    def expected_outcome(self, mu, opp_mu, opp_phi):
        # Calculate win probability using logistic function
        g_val = self.g_phi(opp_phi * self.SCALING_FACTOR)
        return 1.0 / (1.0 + math.exp(-g_val * (mu - opp_mu)))

    def get_variance(self, mu, opponent_ratings, opponent_rds):
        # Calculate statistical variance of the expected outcome
        precision_sum = 0
        for i in range(len(opponent_ratings)):
            opp_mu = (opponent_ratings[i] - 1500) / self.SCALING_FACTOR
            opp_phi = opponent_rds[i] / self.SCALING_FACTOR
            expected = self.expected_outcome(mu, opp_mu, opp_phi)
            g_val = self.g_phi(opponent_rds[i])
            precision_sum += g_val**2 * expected * (1 - expected)
        
        return 1.0 / precision_sum if precision_sum else float('inf')
    
    def get_update_sum(self, mu, opponent_ratings, opponent_rds, outcomes):
        # Sum the differences between actual result and expected probability
        total = 0
        for i in range(len(opponent_ratings)):
            opp_mu = (opponent_ratings[i] - 1500) / self.SCALING_FACTOR
            opp_phi = opponent_rds[i] / self.SCALING_FACTOR
            g_val = self.g_phi(opponent_rds[i])
            total += g_val * (outcomes[i] - self.expected_outcome(mu, opp_mu, opp_phi))
        return total

    def get_improvement(self, v, mu, opponent_ratings, opponent_rds, outcomes):
        # Calculate raw improvement step
        return v * self.get_update_sum(mu, opponent_ratings, opponent_rds, outcomes)

    def calculate_new_volatility(self, delta, phi, v, sigma):
        # Iterative algorithm to find new volatility
        a = math.log(sigma**2)
        delta_sq = delta**2
        
        def f(x):
            ex = math.exp(x)
            term1 = (ex * (delta_sq - phi**2 - v - ex)) / (2 * (phi**2 + v + ex)**2)
            term2 = (x - a) / self.TAU**2
            return term1 - term2

        # Set initial bounds for iteration
        A = a
        if delta_sq > phi**2 + v:
            B = math.log(delta_sq - phi**2 - v)
        else:
            k = 1
            while f(a - k * self.TAU) < 0:
                k += 1
            B = a - k * self.TAU
        
        fA, fB = f(A), f(B)
        
        # Convergence loop
        while abs(B - A) > self.CONVERGENCE_TOLERANCE:
            C = A + (A - B) * fA / (fB - fA)
            fC = f(C)
            if fC * fB < 0:
                A, fA = B, fB
            else:
                fA /= 2
            B, fB = C, fC
            
        return math.exp(A / 2.0)