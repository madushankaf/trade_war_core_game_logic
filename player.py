from payoff import PayOffCalculator
from outcomes import Outcomes
from trade_profile_factory import TradeProfile



class Player:
    def __init__(self, name):
        self.name = name
        self.trade_profile_list: list[TradeProfile] = []


    def add_trade_profile(self, trade_profile: TradeProfile):
        print(f"Adding trade profile: {trade_profile.name} with probability {trade_profile.probability}")
        if sum(profile.probability for profile in self.trade_profile_list) + trade_profile.probability > 1:
            raise ValueError("The sum of trade profile probabilities cannot exceed 1.")
        self.trade_profile_list.append(trade_profile)






