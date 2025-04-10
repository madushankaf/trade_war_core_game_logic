from payoff import PayOffCalculator
from outcomes import Outcomes

us_gdp = 27.07  # in trillion USD
china_gdp = 17.73  # in trillion USD

# us_political_approval = 0.55  # 55% approval rating
# china_political_approval = 0.65  # 65% approval rating
# # Trade balance (in billion USD)
# us_trade_balance = -800  # US has a trade deficit
# china_trade_balance = 800  # China has a trade surplus
# Political boost/loss (in percentage points)
us_political_boost_loss = -5  # US loses 5 percentage points
china_political_boost_loss = 3  # China gains 3 percentage points
# Trade balance shift (in billion USD)
us_trade_balance_shift = 200  # US gains 200 billion USD
china_trade_balance_shift = -200  # China loses 200 billion USD

class Player:
    def __init__(self, name):
        self.name = name
        #self.score = 0
        self.payoffCalculator = PayOffCalculator({
            "GDP_change": 0.7,  # α
            "Political_boost_loss": 1.2,  # β
            "Trade_balance_shift": 0.9  # γ
        })

    def __str__(self):
        return f"Player: {self.name}"


    def cooperate(self, outcomes :Outcomes):
        payoff_value = self.payoffCalculator.calculate_payoff(
            GDP_change=outcomes.getGDP_change(),
            Political_boost_loss=outcomes.getPolitical_boost_loss(),
            Trade_balance_shift=outcomes.getTrade_balance_shift()
        )
        print(f"Payoff for {self.name} (cooperate): {payoff_value}")
        return payoff_value
    
    def defect(self, outcomes :Outcomes):
        payoff_value = self.payoffCalculator.calculate_payoff(
            GDP_change=outcomes.getGDP_change(),
            Political_boost_loss=outcomes.getPolitical_boost_loss(),
            Trade_balance_shift=outcomes.getTrade_balance_shift()
        )
        print(f"Payoff for {self.name} (defect): {payoff_value}")
        return payoff_value
    


# if __name__ == "__main__":
#     usa = Player("USA")
#     china = Player("China")

#     # Example outcomes for the players
#     usa_outcome = {
#         "GDP_change": 2.5,
#         "Political_boost_loss": -3,
#         "Trade_balance_shift": 150
#     }
#     china_outcome = {
#         "GDP_change": 1.5,
#         "Political_boost_loss": 2,
#         "Trade_balance_shift": -150
#     }
#     usa_outcomes = Outcomes(usa_outcome)
#     china_outcomes = Outcomes(china_outcome)

#     # Calculate payoffs for both players
#     usa_payoff = usa.cooperate(usa_outcomes)
#     china_payoff = china.defect(china_outcomes)
#     print(f"USA Payoff: {usa_payoff}")
#     print(f"China Payoff: {china_payoff}")

  
