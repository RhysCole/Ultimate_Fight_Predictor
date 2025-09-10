
class GlickoFighter:
    def __init__(self, rating, rating_deviation, volatility):
        self.rating = rating
        self.rating_deviation = rating_deviation
        self.volatility = volatility

    def __repr__(self) -> str:
        return f"GlickoFighter rating: {self.rating}, rating_deviation: {self.rating_deviation} volatility: {self.volatility}"


    
