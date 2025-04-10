from payoff import PayOff

class Strategy:
    def __init__(self, name, payoff: PayOff):
        self.name = name
        self.payoff = payoff

    def execute(self):
        raise NotImplementedError("You should implement this method.")
    
    def calculate_payoff(self, payoff: PayOff, **kwargs):
        payoff_value = payoff.calculate_payoff(**kwargs)
        return payoff_value
