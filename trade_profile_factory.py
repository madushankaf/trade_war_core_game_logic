from payoff import PayOffCalculator


class TradeProfile:
    def __init__(self, name, gdp_cofficient, political_boost_coefficient, trade_balance_coefficient, probability=0.5):
        """
        Initialize the TradeProfile with coefficients for GDP change, political boost/loss, and trade balance shift.
        
        :param name: Name of the trade profile.
        :param gdp_cofficient: Coefficient for GDP change (α).
        :param political_boost_coefficient: Coefficient for political boost/loss (β).
        :param trade_balance_coefficient: Coefficient for trade balance shift (γ).
        :param probability: Probability of the trade profile being selected (default is 0.5).
        """
        print(f"Creating trade profile: {name} with coefficients: GDP={gdp_cofficient}, Political Boost/Loss={political_boost_coefficient}, Trade Balance Shift={trade_balance_coefficient}")
        self.name = name
        self.gdp_cofficient = gdp_cofficient
        self.political_boost_coefficient = political_boost_coefficient
        self.trade_balance_coefficient = trade_balance_coefficient
        self.probability = probability
        self.pay_off_calculator = PayOffCalculator({
            "GDP_change": gdp_cofficient,
            "Political_boost_loss": political_boost_coefficient,
            "Trade_balance_shift": trade_balance_coefficient
        })

    def calculate_payoff(self):
        """
        Calculate the payoff based on the coefficients and provided aspects.
        
        :param kwargs: Keyword arguments representing aspect values.
        :return: The calculated payoff.
        """
        return self.pay_off_calculator.calculate_payoff(
            GDP_change=self.gdp_cofficient,
            Political_boost_loss=self.political_boost_coefficient,
            Trade_balance_shift=self.trade_balance_coefficient,
            probability=self.probability
        )


        

def create_aggressive_trade_profile(probability=0.5):
    """
    Create an aggressive trade profile with specific coefficients.
    
    α (GDP Δ): Medium / Low
    β (Political): High
    γ (Trade Balance Δ): High
    Interpretation: Focus on political win + strategic trade shifts, willing to hurt GDP.
    
    :return: TradeProfile object with aggressive coefficients.
    """
    return TradeProfile("Aggressive", 0.3, 1.0, 0.9, probability)

def create_dovish_trade_profile(probability=0.5):
    """
    Create a dovish trade profile with specific coefficients.
    
    α (GDP Δ): High
    β (Political): Medium / Low
    γ (Trade Balance Δ): Medium
    Interpretation: Prioritizes economic stability over political noise.
    
    :return: TradeProfile object with dovish coefficients.
    """
    return TradeProfile("Dovish", 0.8, 0.4, 0.6, probability)

def create_strategic_opportunist_trade_profile(probability=0.5):
    """
    Create a strategic opportunist trade profile with specific coefficients.
    
    α (GDP Δ): High
    β (Political): Low
    γ (Trade Balance Δ): High
    Interpretation: Economic gain via neutrality — no political battles.
    
    :return: TradeProfile object with strategic opportunist coefficients.
    """
    return TradeProfile("Strategic Opportunist", 0.9, 0.2, 0.8, probability)

def create_tit_for_tat_trade_profile(probability=0.5):
    """
    Create a tit-for-tat trade profile with specific coefficients.
    
    α (GDP Δ): Balanced
    β (Political): Balanced
    γ (Trade Balance Δ): Balanced
    Interpretation: Equally values deterrence, economic health, and internal standing.
    
    :return: TradeProfile object with tit-for-tat coefficients.
    """
    return TradeProfile("Tit-for-Tat", 0.5, 0.5, 0.5, probability)

def create_isolationist_trade_profile(probability=0.5):
    """
    Create an isolationist trade profile with specific coefficients.
    
    α (GDP Δ): Low
    β (Political): High
    γ (Trade Balance Δ): Medium
    Interpretation: Willing to shrink GDP for sovereignty and self-reliance.
    
    :return: TradeProfile object with isolationist coefficients.
    """
    return TradeProfile("Isolationist", 0.2, 0.9, 0.6, probability)

def create_multilateralist_trade_profile(probability=0.5):
    """
    Create a multilateralist trade profile with specific coefficients.
    
    α (GDP Δ): Medium / High
    β (Political): High (via alliances)
    γ (Trade Balance Δ): Medium
    Interpretation: Focus on GDP via rules-based systems, also earns political points via diplomacy.
    
    :return: TradeProfile object with multilateralist coefficients.
    """
    return TradeProfile("Multilateralist", 0.7, 1.0, 0.6, probability)

def create_adaptive_realist_trade_profile(probability=0.5):
    """
    Create an adaptive realist trade profile with dynamic coefficients.
    
    α (GDP Δ): Variable / Dynamic
    β (Political): Variable
    γ (Trade Balance Δ): Variable
    Interpretation: Parameters shift based on game state or rounds.
    
    :return: TradeProfile object with adaptive realist coefficients.
    """
    # Placeholder values; these would dynamically change in a real implementation
    return TradeProfile("Adaptive Realist", 0.5, 0.5, 0.5, probability)

def create_symbolic_player_trade_profile(probability=0.5):
    """
    Create a symbolic player trade profile with specific coefficients.
    
    α (GDP Δ): Low
    β (Political): Very High
    γ (Trade Balance Δ): Low
    Interpretation: Gains are mostly political and short-term symbolic.
    
    :return: TradeProfile object with symbolic player coefficients.
    """
    return TradeProfile("Symbolic Player", 0.2, 1.0, 0.3, probability)
