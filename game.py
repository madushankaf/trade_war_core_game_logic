from player import Player
from outcomes import Outcomes  # Assuming Outcomes is defined in a separate module
import nashpy as nash
import numpy as np
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

import numpy as np
from scipy.optimize import linprog

def solve_mixed_strategy_indifference_row_player_only_general(player1_payoffs):
    """
    Solves for a mixed strategy for Player 2 that makes Player 1 indifferent between all their pure strategies.

    Arguments:
        player1_payoffs: numpy array of shape (m, n) representing Player 1's payoff matrix.

    Returns:
        A numpy array of length n representing Player 2's mixed strategy, or np.nan array if no valid solution exists.
    """
    A = player1_payoffs
    m, n = A.shape

    if m < 2:
        raise ValueError("Need at least two strategies for the row player.")

    # Create (m-1) indifference equations: (A[i] - A[0]) · p = 0
    equations = A[1:] - A[0:1]

    # Final system: equations @ p = 0, and sum(p) = 1
    lhs_eq = np.vstack([equations, np.ones((1, n))])
    rhs_eq = np.zeros(m)
    rhs_eq[-1] = 1  # The sum constraint

    # Solve using linear programming to enforce p >= 0
    # Objective is irrelevant — just find a feasible solution
    res = linprog(
        c=np.zeros(n),
        A_eq=lhs_eq,
        b_eq=rhs_eq,
        bounds=[(0, 1)] * n,
        method='highs'
    )

    if res.success and np.isclose(np.sum(res.x), 1):
        return res.x
    else:
        return np.full(n, np.nan)


def solve_mixed_strategy_indifference_col_player_only_general(player2_payoffs):
    """
    Solves for a mixed strategy for Player 1 that makes Player 2 indifferent between all their pure strategies.

    Arguments:
        player2_payoffs: numpy array of shape (m, n) representing Player 2's payoff matrix.

    Returns:
        A numpy array of length m representing Player 1's mixed strategy, or np.nan array if no valid solution exists.
    """
    A = player2_payoffs
    m, n = A.shape

    if n < 2:
        raise ValueError("Need at least two strategies for the column player.")

    # Create (n-1) indifference equations: (A[:, i] - A[:, 0]) · p = 0
    equations = A[:, 1:] - A[:, 0:1]

    # Final system: equations @ p = 0, and sum(p) = 1
    lhs_eq = np.vstack([equations.T, np.ones((1, m))])
    rhs_eq = np.zeros(n)
    rhs_eq[-1] = 1  # The sum constraint

    # Solve using linear programming to enforce p >= 0
    res = linprog(
        c=np.zeros(m),
        A_eq=lhs_eq,
        b_eq=rhs_eq,
        bounds=[(0, 1)] * m,
        method='highs'
    )

    if res.success and np.isclose(np.sum(res.x), 1):
        return res.x
    else:
        return np.full(m, np.nan)









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
        r, c = eq
        print (f" Nash Equilibrium: {r @ player1_payoffs @ c.T}, {c}")
        print (f" Nash Equilibrium: {r @ player2_payoffs @ c.T}, {c}")

    

    probabability_of_player2_that_makes_player1_indifferent = solve_mixed_strategy_indifference_row_player_only_general(np.array(player1_payoffs))
    print("Mixed Strategy Probability for  Player 2:", probabability_of_player2_that_makes_player1_indifferent)
    probabability_of_player1_that_makes_player2_indifferent = solve_mixed_strategy_indifference_col_player_only_general(np.array(player2_payoffs))
    print("Mixed Strategy Probability for Player 1:", probabability_of_player1_that_makes_player2_indifferent)
    

    
    # Checking best responses
    # strategies = np.linspace(0, 1, 11)  # Probabilities from 0 to 1 in steps of 0.1
    # for p1_prob in strategies:
    #     for p2_prob in strategies:
    #         p1_strategy = [p1_prob, 1 - p1_prob]  # Player 1's mixed strategy
    #         p2_strategy = [p2_prob, 1 - p2_prob]  # Player 2's mixed strategy
            
    #         is_p1_best_response = game_nash.is_best_response(np.array(p1_strategy), np.array(p2_strategy))
    #         is_p2_best_response = game_nash.is_best_response(np.array(p2_strategy), np.array(p1_strategy))

            
    #         print(f"Player 1 Strategy: {p1_strategy}, Player 2 Strategy: {p2_strategy}")
    #         print(f"Is Player 1 Best Response: {is_p1_best_response}")
    #         print(f"Is Player 2 Best Response: {is_p2_best_response}")
    #         print("-" * 50)
    #         game_nash[np.array(p1_strategy), np.array(p2_strategy)]
    #         for eq in game_nash.support_enumeration():
    #             print("Mixed Nash Equilibrium:", eq)

    # for eq in game_nash.vertex_enumeration():
    #     print("Nash Equilibrium (Vertex Enumeration):", eq)


    
   
