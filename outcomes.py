class Outcomes:
    def __init__(self, outcome):
        self.outcome = outcome
        self.GDP_change = outcome.get("GDP_change", 0)
        self.Political_boost_loss = outcome.get("Political_boost_loss", 0)
        self.Trade_balance_shift = outcome.get("Trade_balance_shift", 0)


    def getGDP_change(self):
        return self.GDP_change
    
    def getPolitical_boost_loss(self):
        return self.Political_boost_loss
    
    def getTrade_balance_shift(self):
        return self.Trade_balance_shift

