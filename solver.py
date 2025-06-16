import nashpy as nash
import numpy as np
from scipy.optimize import linprog
from trade_profile_factory import TradeProfile
from outcomes import Outcomes



def generate_probabiliies():
    return np.linspace(0, 1, 11)



def find_all_nash_equilibria(row_player_payoffs, col_player_payoffs):
    """
    Finds all Nash equilibria for a given game using the support enumeration method.oi 
    
    Arguments:
        row_player_payoffs: numpy array of shape (m, n) representing the payoff matrix for the row player.
        col_player_payoffs: numpy array of shape (m, n) representing the payoff matrix for the column player.
    
    Returns:
        A list of tuples, where each tuple contains two numpy arrays representing the mixed strategies of the row and column players.
    """
    game = nash.Game(row_player_payoffs, col_player_payoffs)

    strategies = []
    for eq in game.support_enumeration():
        row_strategy, col_strategy = eq
        print(f"Row Strategy: {row_strategy}, Column Strategy: {col_strategy}")
        strategies.append((row_strategy, col_strategy))
    return strategies


def solve_mixed_strategy_indifference_general(payoffs, player='row'):
    """
    Solves for a mixed strategy for one player that makes the other player indifferent between all their pure strategies.

    Arguments:
        payoffs: numpy array of shape (m, n) representing the payoff matrix for the player whose strategies are being solved.
        player: 'row' to solve for the column player's mixed strategy (making the row player indifferent),
                'col' to solve for the row player's mixed strategy (making the column player indifferent).

    Returns:
        A numpy array representing the mixed strategy for the specified player, or np.nan array if no valid solution exists.
    """
    A = payoffs
    m, n = A.shape

    if player == 'row':
        if m < 2:
            raise ValueError("Need at least two strategies for the row player.")
        # Create (m-1) indifference equations: (A[i] - A[0]) · p = 0
        equations = A[1:] - A[0:1]
        lhs_eq = np.vstack([equations, np.ones((1, n))])
        rhs_eq = np.zeros(m)
        rhs_eq[-1] = 1  # The sum constraint
        bounds = [(0, 1)] * n
        c = np.zeros(n)
    elif player == 'col':
        if n < 2:
            raise ValueError("Need at least two strategies for the column player.")
        # Create (n-1) indifference equations: (A[:, i] - A[:, 0]) · p = 0
        equations = A[:, 1:] - A[:, 0:1]
        lhs_eq = np.vstack([equations.T, np.ones((1, m))])
        rhs_eq = np.zeros(n)
        rhs_eq[-1] = 1  # The sum constraint
        bounds = [(0, 1)] * m
        c = np.zeros(m)
    else:
        raise ValueError("Player must be 'row' or 'col'.")

    # Solve using linear programming to enforce p >= 0
    res = linprog(
        c=c,
        A_eq=lhs_eq,
        b_eq=rhs_eq,
        bounds=bounds,
        method='highs'
    )

    if res.success and np.isclose(np.sum(res.x), 1):
        return res.x
    else:
        return np.full(len(c), np.nan)
    



def generate_payoff_matrix_for_given_trade_profile_and_stategy_outcome( outcome: Outcomes, trade_profle: TradeProfile):
    """
    Generates a payoff matrix for a given trade profile and strategy outcome.
    Arguments:
        trade_profile: TradeProfile object representing the trade profile.
        outcome: Outcomes object representing the strategy outcome.
    Returns:
        calculated_payoff: The calculated payoff based on the trade profile and outcome.

    """
    # Placeholder for actual implementation
    # This function should create a payoff matrix based on the trade profile and outcome.
    # For now, we'll just return a dummy matrix.

    return trade_profle.calculate_payoff(
        GDP_change=outcome.gdp_change,
        Political_boost_loss=outcome.political_boost_loss,
        Trade_balance_shift=outcome.trade_balance_shift
    )



def calculate_total_probability_of_a_given_action(action: str, trade_profile: TradeProfile):
    """
    Calculates the total probability of a given action in the context of a trade profile.
    
    Arguments:
        action: The action for which the probability is to be calculated.
        trade_profile: TradeProfile object representing the trade profile.
    
    Returns:
        total_probability: The total probability of the given action.
    """
    # Placeholder for actual implementation
    # This function should calculate the total probability based on the trade profile and action.
    # For now, we'll just return the prior probability of the trade profile.

    return trade_profile.probability

def calculate_total_probability_of_a_given_trade_profile(trade_profile: TradeProfile, action: str):
    """
    Calculates the total probability of a given trade profile.
    """

    prior_probability = trade_profile.probability

    return trade_profile.calculate_total_probability()


if __name__ == "__main__":
    # Example usage
    row_player_payoffs = np.array([[133.15, 84.7], [-86.7, 33.35]])
    col_player_payoffs = np.array([[-131.55, -86.7], [84.7, -56.65]])

    col_mix = solve_mixed_strategy_indifference_general(row_player_payoffs, player='row')
    row_mix = solve_mixed_strategy_indifference_general(col_player_payoffs, player='col')

    # print(f"Row Player Mixed Strategy: {row_strategy}")
    # print(f"Column Player Mixed Strategy: {col_strategy}")

    # row_player_mixed_payoff = row_player_payoffs @ row_strategy
    # col_player_mixed_payoff = col_player_payoffs @ col_strategy
    # print(f"Row Player Mixed Payoff: {row_player_mixed_payoff}")
    # print(f"Column Player Mixed Payoff: {col_player_mixed_payoff}")

    all_NEs = find_all_nash_equilibria(row_player_payoffs, col_player_payoffs)
    for row_strategy, col_strategy in all_NEs:
        row_is_pure = np.isclose(np.sum(row_strategy == 1), 1)
        col_is_pure = np.isclose(np.sum(col_strategy == 1), 1)

        if row_is_pure:
            print(f"Row Strategy: {row_strategy} (Pure)")
        else:
            print(f"Row Strategy: {row_strategy}")

        if col_is_pure:
            print(f"Column Strategy: {col_strategy} (Pure)")
        else:
            print(f"Column Strategy: {col_strategy}")

        row_player_mixed_payoff = row_strategy @ row_player_payoffs @ col_strategy.T
        col_player_mixed_payoff = row_strategy @ col_player_payoffs @ col_strategy.T
        print(f"Row Player Mixed Payoff: {row_player_mixed_payoff}")
        print(f"Column Player Mixed Payoff: {col_player_mixed_payoff}")


    

    
