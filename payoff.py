

class PayOffCalculator:
    def __init__(self, weights):
        """
        Initialize the PayOff class with a dictionary of weights.
        :param weights: A dictionary where keys are aspect names and values are their weights.
        """
        self.weights = weights

    def calculate_payoff(self, **aspects):
        """
        Calculate the payoff based on the provided aspects and their weights.
        :param aspects: Keyword arguments representing aspect values.
        :return: The calculated payoff.
        """
        return sum(self.weights.get(key, 0) * value for key, value in aspects.items())

    def __str__(self):
        return f"PayOff(weights={self.weights})"

    def __repr__(self):
        return f"PayOff(weights={self.weights})"
    


# Example usage
# if __name__ == "__main__":
#     # Define weights for different aspects
#     weights = {
#         "GDP_change": 0.7,  # α
#         "Political_boost_loss": 1.2,  # β
#         "Trade_balance_shift": 0.9  # γ
#     }

#     # Create a PayOff object
#     payoff = PayOffCalculator(weights)

#     # Calculate payoff for given aspects
#     result = payoff.calculate_payoff(
#         GDP_change=3.5, 
#         Political_boost_loss=-1.0, 
#         Trade_balance_shift=2.0
#     )
#     print(f"Calculated Payoff: {result}")
