from player import Player
from outcomes import Outcomes  # Assuming Outcomes is defined in a separate module

class Game:
    def __init__(self, player1: Player, player2: Player):
        self.player1 = player1
        self.player2 = player2

    def simulate_strategy(self, strategy1, strategy2):
        # Define outcomes for each strategy combination
        outcomes = {
            ("cooperate", "cooperate"): (
            Outcomes({"GDP_change": 2.5, "Political_boost_loss": -3, "Trade_balance_shift": 150}),
            Outcomes({"GDP_change": 1.5, "Political_boost_loss": 2, "Trade_balance_shift": -150}),
            ),
            ("cooperate", "defect"): (
            Outcomes({"GDP_change": 1.0, "Political_boost_loss": -5, "Trade_balance_shift": 100}),
            Outcomes({"GDP_change": 3.0, "Political_boost_loss": 1, "Trade_balance_shift": -100}),
            ),
            ("defect", "cooperate"): (
            Outcomes({"GDP_change": 3.0, "Political_boost_loss": 1, "Trade_balance_shift": -100}),
            Outcomes({"GDP_change": 1.0, "Political_boost_loss": -5, "Trade_balance_shift": 100}),
            ),
            ("defect", "defect"): (
            Outcomes({"GDP_change": 0.5, "Political_boost_loss": -10, "Trade_balance_shift": 50}),
            Outcomes({"GDP_change": 0.5, "Political_boost_loss": -10, "Trade_balance_shift": -50}),
            ),
        }

        player1_outcome, player2_outcome = outcomes[(strategy1, strategy2)]
        player1_payoff = self.player1.cooperate(player1_outcome) if strategy1 == "cooperate" else self.player1.defect(player1_outcome)
        player2_payoff = self.player2.cooperate(player2_outcome) if strategy2 == "cooperate" else self.player2.defect(player2_outcome)

        return player1_payoff, player2_payoff

    def play(self):
        strategies = ["cooperate", "defect"]
        payoff_matrix = {}
        player1_payoffs = []
        player2_payoffs = []

        for strategy1 in strategies:
            row1 = []
            row2 = []
            for strategy2 in strategies:
                player1_payoff, player2_payoff = self.simulate_strategy(strategy1, strategy2)
                payoff_matrix[(strategy1, strategy2)] = (player1_payoff, player2_payoff)
                row1.append(player1_payoff)
                row2.append(player2_payoff)
            player1_payoffs.append(row1)
            player2_payoffs.append(row2)

        print("Payoff Matrix:")
        for strategy1 in strategies:
            row = []
            for strategy2 in strategies:
                row.append(payoff_matrix[(strategy1, strategy2)])
            print(f"{strategy1}: {row}")

        print("\nPlayer 1 Payoffs:")
        for row in player1_payoffs:
            print(row)

        print("\nPlayer 2 Payoffs:")
        for row in player2_payoffs:
            print(row)

        return payoff_matrix, player1_payoffs, player2_payoffs
    

    
    
 

import numpy as np
import nashpy as nash


if __name__ == "__main__":
    # Example usage
    usa = Player("USA")
    china = Player("China")

    game = Game(usa, china)    
    payoff_matrix, player1_payoffs, player2_payoffs = game.play()
    print("Payoff Matrix:", payoff_matrix)
    print("USA Payoffs:", player1_payoffs)
    print("China Payoffs:", player2_payoffs)



    game_nash = nash.Game(np.array(player1_payoffs), np.array(player2_payoffs))
    for eq in game_nash.support_enumeration():
        print("Nash Equilibrium:", eq)

    
    # Checking best responses
    strategies = np.linspace(0, 1, 11)  # Probabilities from 0 to 1 in steps of 0.1
    for p1_prob in strategies:
        for p2_prob in strategies:
            p1_strategy = [p1_prob, 1 - p1_prob]  # Player 1's mixed strategy
            p2_strategy = [p2_prob, 1 - p2_prob]  # Player 2's mixed strategy
            
            is_p1_best_response = game_nash.is_best_response(np.array(p1_strategy), np.array(p2_strategy))
            is_p2_best_response = game_nash.is_best_response(np.array(p2_strategy), np.array(p1_strategy))
            
            print(f"Player 1 Strategy: {p1_strategy}, Player 2 Strategy: {p2_strategy}")
            print(f"Is Player 1 Best Response: {is_p1_best_response}")
            print(f"Is Player 2 Best Response: {is_p2_best_response}")
            print("-" * 50)

    for eq in game_nash.vertex_enumeration():
        print("Nash Equilibrium (Vertex Enumeration):", eq)
    
   
